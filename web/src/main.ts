/**
 * OpenHandTrack webcam demo entry point.
 *
 * Wires up: getUserMedia -> HandTracker -> requestAnimationFrame detection
 * loop -> canvas rendering with one-euro smoothing. The whole demo is these
 * ~90 lines on top of the library.
 */

import "./style.css";
import { HandTracker, type HandResult } from "./tracker";
import { drawHandResult } from "./render";

const video = document.querySelector<HTMLVideoElement>("#camera")!;
const canvas = document.querySelector<HTMLCanvasElement>("#overlay")!;
const statusText = document.querySelector<HTMLDivElement>("#status")!;
const ctx = canvas.getContext("2d")!;

const tracker = new HandTracker({
  maxHands: 2,
  // HTMLVideoElement delivers unmirrored pixels, so the wrapper swaps
  // MediaPipe's handedness to physical labels (mirrored defaults to false).
  smoothing: true,
});

let lastFrameTime = performance.now();
let fps = 0;
let pendingFrames = 0;

function setStatus(html: string, kind: "info" | "warn" | "error" = "info") {
  statusText.className = kind;
  statusText.innerHTML = html;
}

async function startCamera(): Promise<void> {
  if (!navigator.mediaDevices?.getUserMedia) {
    throw new Error("getUserMedia is not supported in this browser.");
  }

  // facingMode "user" prefers the front camera — works on phones too.
  const stream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } },
    audio: false,
  });
  video.srcObject = stream;
  await video.play();
}

function startLoop(): void {
  const tick = (now: number) => {
    requestAnimationFrame(tick);

    // Throttle work when the tab is hidden (saves battery on laptops).
    if (document.hidden) return;

    pendingFrames++;
    if (pendingFrames < 2) return; // skip if we fell behind (matches video fps)
    pendingFrames = 0;

    fps = 0.9 * fps + 0.1 * (1000 / Math.max(now - lastFrameTime, 1));
    lastFrameTime = now;

    const result: HandResult = tracker.detectForVideo(video);
    drawHandResult(ctx, video, result, { showLabels: true });

    if (result.isEmpty) {
      setStatus("No hand in frame — hold your hand up");
    } else {
      const labels = result.hands.map((h) => h.handedness).join(" + ");
      setStatus(
        `${result.hands.length} hand${result.hands.length > 1 ? "s" : ""}: ${labels} · ${fps.toFixed(0)} fps`,
      );
    }
  };
  requestAnimationFrame(tick);
}

async function main(): Promise<void> {
  setStatus("Loading hand-tracking model…");
  try {
    await tracker.initialize();
  } catch (err) {
    setStatus(
      `Failed to load the model (network?). Check the console and reload. ${String(err)}`,
      "error",
    );
    throw err;
  }

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

  // Size the canvas to the live video, not the CSS box, so the skeleton
  // lines up pixel-perfectly (handles devicePixelRatio on phones).
  const onVideoReady = () => {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
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
