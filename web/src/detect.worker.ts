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
}

export interface WorkerFrame {
  type: "frame";
  bitmap: ImageBitmap;
  timestampMs: number;
}

export type WorkerOut =
  | { type: "ready" }
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

self.onmessage = async (event: MessageEvent<WorkerInit | WorkerFrame>) => {
  const msg = event.data;

  if (msg.type === "init") {
    try {
      const fileset = await FilesetResolver.forVisionTasks(msg.wasmBase);
      const make = (delegate: "GPU" | "CPU") =>
        HandLandmarker.createFromOptions(fileset, {
          baseOptions: { modelAssetPath: msg.modelUrl, delegate },
          runningMode: "VIDEO",
          numHands: msg.maxHands,
          minHandDetectionConfidence: 0.5,
          minHandPresenceConfidence: 0.5,
          minTrackingConfidence: 0.5,
        });
      try {
        landmarker = await make("GPU");
      } catch {
        // old drivers / software-GL contexts sometimes reject the GPU graph
        landmarker = await make("CPU");
      }
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
    } catch (err) {
      out = { type: "error", message: String(err) };
    }
    msg.bitmap.close();
    (self as unknown as Worker).postMessage(out);
  }
};
