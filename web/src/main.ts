/**
 * OpenHandTrack webcam demo entry point.
 *
 * Architecture (tuned for weak GPUs):
 *   <video> plays natively — the compositor shows it at full frame rate.
 *   A Web Worker owns ALL inference; the main thread never blocks.
 *   The canvas is a transparent overlay that draws only the skeleton,
 *   interpolating landmarks between detections so motion stays fluid even
 *   when the GPU manages only a few inferences per second.
 */

import "./style.css";
import { LandmarkSmoother } from "./smoothing";
import { drawHand } from "./render";
import type { WorkerInit, WorkerOut } from "./detect.worker";

const video = document.querySelector<HTMLVideoElement>("#camera")!;
const canvas = document.querySelector<HTMLCanvasElement>("#overlay")!;
const statusText = document.querySelector<HTMLDivElement>("#status")!;
const ctx = canvas.getContext("2d")!;

const MODEL_URL =
  "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task";
// Same-origin WASM copied from node_modules at build time (web/public/mediapipe/wasm).
// A CDN path risks glue/binary version drift -> cryptic "ModuleFactory not set".
const WASM_BASE = new URL("mediapipe/wasm", location.href).href;

interface TrackedHand {
  landmarks: { x: number; y: number; z: number }[];
  handedness: "Left" | "Right";
  confidence: number;
}

// CSS mirrors both #camera and #overlay (scaleX(-1)) giving the user a
// selfie view. MediaPipe labels handedness assuming mirrored input, so its
// raw labels already match the mirrored display — no swapping needed.
const smoother = new LandmarkSmoother();
let latestHands: TrackedHand[] = [];
let shownHands: TrackedHand[] = []; // eased toward latest every frame
let prevHands: TrackedHand[] = []; // pose we're easing FROM
let lastResultTime = 0;

const cloneHand = (h: TrackedHand): TrackedHand => ({
  ...h,
  landmarks: h.landmarks.map((p) => ({ ...p })),
});
const cloneHands = (hs: TrackedHand[]): TrackedHand[] => hs.map(cloneHand);

/**
 * Landmark interpolation between detections: shown = lerp(prev → latest).
 *
 * The easing window tracks the actual measurement cadence (detectIntervalMs),
 * so at ~8 Hz tracking each new pose is reached exactly when the next one
 * arrives — the skeleton glides continuously instead of stepping. When no
 * result has arrived yet we ease from wherever we were toward the newest
 * pose with a fixed 120 ms tail so hands don't teleport on re-acquisition.
 */
function interpolateToLatest(now: number): void {
  if (latestHands.length === 0) {
    shownHands = [];
    prevHands = [];
    return;
  }

  const span = Math.max(lastResultTime - lastSentTime, 40);
  // Start halfway to the new pose (responsive) and land exactly as the next
  // measurement is expected — a continuous glide, never a snap.
  const raw = Math.min(1, Math.max(0, (now - lastResultTime) / span));
  const t = 0.5 + 0.5 * raw;
  const k = 1 - Math.pow(1 - t, 2); // ease-out quad

  shownHands = latestHands.map((hand) => {
    const from =
      prevHands.find((p) => p.handedness === hand.handedness) ?? hand;
    return {
      handedness: hand.handedness,
      confidence: hand.confidence,
      landmarks: hand.landmarks.map((to, j) => {
        const a = from.landmarks[j] ?? to;
        return {
          x: a.x + (to.x - a.x) * k,
          y: a.y + (to.y - a.y) * k,
          z: a.z + (to.z - a.z) * k,
        };
      }),
    };
  });
}

const worker = new Worker(new URL("./detect.worker.ts", import.meta.url), {
  type: "module",
});

function post(msg: WorkerInit) {
  worker.postMessage(msg);
}

// --- adaptive detection cadence ---------------------------------------------
// We ask the worker how long each inference took and adjust our request rate
// so a slow GPU lowers the tracking Hz instead of stuttering anything.
let detectIntervalMs = 50;
let lastSentTime = 0;
let detectHz = 0;
let busy = false;
let workerReady = false; // model loaded — safe to send frames

function tuneInterval(measuredMs: number): void {
  if (measuredMs > 35) {
    detectIntervalMs = Math.min(200, detectIntervalMs + 20);
  } else if (measuredMs < 18 && detectIntervalMs > 50) {
    detectIntervalMs -= 5;
  }
}

worker.onmessage = (event: MessageEvent<WorkerOut>) => {
  const msg = event.data;
  if (msg.type === "ready") {
    workerReady = true;
    setStatus("Camera starting…");
  } else if (msg.type === "error") {
    setStatus(`Tracker error: ${msg.message}`, "error");
  } else if (msg.type === "result") {
    tuneInterval(msg.detectMs);
    detectHz = 0.8 * detectHz + 0.2 * (1000 / Math.max(detectIntervalMs, 1));
    // Keep the previous pose so the render loop can ease toward the new one
    // instead of snapping — this is what makes low tracking rates look fluid.
    prevHands = shownHands.length ? cloneHands(shownHands) : latestHands.map(cloneHand);
    latestHands = smoother.update(msg.hands) as TrackedHand[];
    lastResultTime = performance.now();
  }
  // Whatever came back (result/error/ready), the pipeline is free again.
  busy = false;
};

function maybeSendFrame(now: number): void {
  if (busy || !workerReady || video.readyState < 2) return;
  if (now - lastSentTime < detectIntervalMs) return;
  // createImageBitmap is async GPU-side copy — cheap on the main thread.
  createImageBitmap(video)
    .then((bitmap) => {
      busy = true;
      lastSentTime = performance.now();
      worker.postMessage({ type: "frame", bitmap, timestampMs: lastSentTime }, [
        bitmap,
      ]);
    })
    .catch(() => {});
}

// --- render loop (skeleton only — video plays underneath) --------------------
let lastFrameTime = performance.now();
let fps = 0;

declare const __BUILD_ID__: string;

function setStatus(html: string, kind: "info" | "warn" | "error" = "info") {
  statusText.className = kind;
  statusText.innerHTML = html;
}

async function startCamera(): Promise<void> {
  if (!navigator.mediaDevices?.getUserMedia) {
    throw new Error("getUserMedia is not supported in this browser.");
  }
  // Inference cost scales with pixels; 360p tracks hands just as well for an
  // overlay demo and keeps integrated GPUs comfortable.
  const stream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 360 } },
    audio: false,
  });
  video.srcObject = stream;
  await video.play();
}

function startLoop(): void {
  const tick = (now: number) => {
    requestAnimationFrame(tick);

    if (document.hidden) return;

    fps = 0.9 * fps + 0.1 * (1000 / Math.max(now - lastFrameTime, 1));
    lastFrameTime = now;

    maybeSendFrame(now);
    interpolateToLatest(now);

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (const hand of shownHands) {
      drawHand(ctx, hand, { showLabels: true });
    }

    if (latestHands.length === 0) {
      setStatus("No hand in frame — hold your hand up");
    } else {
      const labels = latestHands.map((h) => h.handedness).join(" + ");
      setStatus(
        `${latestHands.length} hand${latestHands.length > 1 ? "s" : ""}: ${labels} · ` +
          `${fps.toFixed(0)} fps · track ${detectHz.toFixed(0)} Hz`,
      );
    }
  };
  requestAnimationFrame(tick);
}

async function main(): Promise<void> {
  setStatus(`build ${__BUILD_ID__} · loading model…`);

  post({
    type: "init",
    modelUrl: MODEL_URL,
    wasmBase: WASM_BASE,
    maxHands: 2,
  });

  try {
    await startCamera();
  } catch (err) {
    setStatus(
      "No webcam found or camera permission denied. This demo needs a camera.",
      "error",
    );
    console.error(err);
    return;
  }

  // Size the overlay to the CSS display box at 1x — retina backing stores
  // multiply fill cost by dpr² for zero benefit here.
  const onVideoReady = () => {
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.round(rect.width);
    canvas.height = Math.round(rect.height);
    video.removeEventListener("loadedmetadata", onVideoReady);
    startLoop();
  };
  if (video.videoWidth > 0) onVideoReady();
  else video.addEventListener("loadedmetadata", onVideoReady);
}

main().catch((err) => {
  console.error(err);
  setStatus(`Unexpected error: ${String(err)}`, "error");
});
