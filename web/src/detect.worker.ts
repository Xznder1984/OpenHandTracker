/**
 * Inference worker — runs the MediaPipe HandLandmarker OFF the main thread.
 *
 * The main thread sends `createImageBitmap(video)` frames; we run detection
 * here (slow on weak GPUs, but that no longer matters) and post back plain
 * landmark arrays. The UI keeps rendering at full frame rate regardless of
 * how long inference takes — no more blocked paints.
 */

import { FilesetResolver, HandLandmarker } from "@mediapipe/tasks-vision";

export interface WorkerInit {
  type: "init";
  modelUrl: string;
  wasmBase: string;
  maxHands: 1 | 2;
  /** Force a delegate ("GPU"/"CPU"); omit for GPU→CPU auto with runtime watchdog. */
  delegate?: "GPU" | "CPU";
}

export interface WorkerFrame {
  type: "frame";
  bitmap: ImageBitmap;
  timestampMs: number;
}

export type WorkerOut =
  | { type: "ready" }
  | { type: "delegateFallback"; delegate: "GPU" | "CPU" }
  | {
      type: "result";
      hands: {
        landmarks: { x: number; y: number; z: number }[];
        handedness: "Left" | "Right";
        confidence: number;
      }[];
      detectMs: number;
    }
  | { type: "error"; message: string };

let landmarker: HandLandmarker | null = null;
// Watchdog state: some Intel iGPUs create a GPU context that inits fine but
// silently returns zero detections. If enough consecutive frames yield no
// hands, rebuild the graph on CPU — inference is slower but off-thread, so
// the UI never notices beyond a lower tracking rate.
const EMPTY_STREAK_LIMIT = 10;
let emptyStreak = 0;
let activeDelegate: "GPU" | "CPU" | null = null;
let initOptions: WorkerInit | null = null;

async function buildLandmarker(
  fileset: Awaited<ReturnType<typeof FilesetResolver.forVisionTasks>>,
  forced: "GPU" | "CPU" | undefined,
): Promise<"GPU" | "CPU"> {
  const make = (delegate: "GPU" | "CPU") =>
    HandLandmarker.createFromOptions(fileset, {
      baseOptions: { modelAssetPath: initOptions!.modelUrl, delegate },
      runningMode: "VIDEO",
      numHands: initOptions!.maxHands,
      minHandDetectionConfidence: 0.5,
      minHandPresenceConfidence: 0.5,
      minTrackingConfidence: 0.5,
    });
  if (forced) {
    landmarker = await make(forced);
    return forced;
  }
  try {
    landmarker = await make("GPU");
    return "GPU";
  } catch {
    // old drivers / software-GL contexts sometimes reject the GPU graph
    landmarker = await make("CPU");
    return "CPU";
  }
}

self.onmessage = async (event: MessageEvent<WorkerInit | WorkerFrame>) => {
  const msg = event.data;

  if (msg.type === "init") {
    try {
      initOptions = msg;
      const fileset = await FilesetResolver.forVisionTasks(msg.wasmBase);
      activeDelegate = await buildLandmarker(fileset, msg.delegate);
      (self as unknown as Worker).postMessage({ type: "ready" } satisfies WorkerOut);
    } catch (err) {
      (self as unknown as Worker).postMessage({
        type: "error",
        message: String(err),
      } satisfies WorkerOut);
    }
    return;
  }

  if (msg.type === "frame") {
    if (!landmarker) {
      // Model still loading: acknowledge with an empty result so the main
      // thread can never deadlock waiting for a reply that never comes.
      msg.bitmap.close();
      (self as unknown as Worker).postMessage({
        type: "result",
        hands: [],
        detectMs: 0,
      } satisfies WorkerOut);
      return;
    }
    const t0 = performance.now();
    let out: WorkerOut;
    try {
      const res = landmarker.detectForVideo(msg.bitmap, msg.timestampMs);
      const detectMs = performance.now() - t0;
      const hands = (res.landmarks ?? []).map((pts, i) => ({
        landmarks: pts,
        handedness:
          (res.handednesses?.[i]?.[0]?.categoryName === "Left" ? "Left" : "Right") as
            | "Left"
            | "Right",
        confidence: res.handednesses?.[i]?.[0]?.score ?? 0,
      }));
      out = { type: "result", hands, detectMs };

      // GPU watchdog: real frames keep flowing, but if the graph keeps seeing
      // nothing while running on GPU, the context is likely silently broken —
      // rebuild once on CPU and tell the UI what happened.
      if (activeDelegate === "GPU") {
        emptyStreak = hands.length === 0 ? emptyStreak + 1 : 0;
        if (emptyStreak >= EMPTY_STREAK_LIMIT && initOptions) {
          emptyStreak = 0;
          try {
            const fileset = await FilesetResolver.forVisionTasks(initOptions.wasmBase);
            landmarker?.close();
            landmarker = null;
            activeDelegate = await buildLandmarker(fileset, "CPU");
            (self as unknown as Worker).postMessage({
              type: "delegateFallback",
              delegate: activeDelegate,
            } satisfies WorkerOut);
          } catch {
            /* keep serving GPU results; nothing better available */
          }
        }
      }
    } catch (err) {
      out = { type: "error", message: String(err) };
    }
    msg.bitmap.close();
    (self as unknown as Worker).postMessage(out);
  }
};
