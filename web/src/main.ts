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

// CSS mirrors both #camera and #overlay (scaleX(-1)) giving the user a
// selfie view.  MediaPipe processes the raw unmirrored frames and labels
// handedness assuming mirrored input — so its raw labels are already
// correct for the mirrored display.  `mirrored: true` = "treat input as
// mirrored" = don't swap the labels.
const tracker = new HandTracker({
  maxHands: 2,
  mirrored: true,
  smoothing: true,
});

// --- throttled detection loop ------------------------------------------------
// `detectForVideo` is synchronous WASM work that blocks the main thread.
// To keep the UI smooth we cap inference at ~30 fps and reuse the last
// detection result for the frames in between.
const DETECT_INTERVAL_MS = 33; // ~30 fps detection cap
let lastDetectTime = 0;
let lastResult: HandResult | null = null;

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

    fps = 0.9 * fps + 0.1 * (1000 / Math.max(now - lastFrameTime, 1));
    lastFrameTime = now;

    // Run detection at most every DETECT_INTERVAL_MS; between detections
    // reuse the previous result so the skeleton stays visible and smooth.
    let result: HandResult;
    if (now - lastDetectTime >= DETECT_INTERVAL_MS || lastResult === null) {
      result = tracker.detectForVideo(video);
      lastResult = result;
      lastDetectTime = now;
    } else {
      result = lastResult;
    }

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

  // Size the canvas to the CSS display size (not the full video resolution)
  // so drawImage + skeleton rendering stay cheap on high-res webcams.
  const onVideoReady = () => {
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.round(rect.width * devicePixelRatio);
    canvas.height = Math.round(rect.height * devicePixelRatio);
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
