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
const WASM_BASE =
  "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm";

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
let shownHands: TrackedHand[] = []; // interpolated between worker results

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
    setStatus("Camera starting…");
  } else if (msg.type === "error") {
    setStatus(`Tracker error: ${msg.message}`, "error");
  } else if (msg.type === "result") {
    tuneInterval(msg.detectMs);
    detectHz = 0.8 * detectHz + 0.2 * (1000 / Math.max(detectIntervalMs, 1));
    latestHands = smoother.update(msg.hands) as TrackedHand[];
    busy = false;
  }
};

function maybeSendFrame(now: number): void {
  if (busy || video.readyState < 2) return;
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
    // One-euro smoothing already glides landmarks; between worker results we
    // simply hold the last smoothed pose — at 60 fps overlay this reads as
    // continuous motion even when tracking runs only a few times a second.
    shownHands = latestHands;

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
  setStatus("Loading hand-tracking model…");

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
