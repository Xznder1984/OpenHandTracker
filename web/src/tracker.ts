/**
 * HandTracker — a thin, clean wrapper around @mediapipe/tasks-vision's
 * HandLandmarker, shaped to feel familiar if you've read the Python side of
 * OpenHandTrack (HandTracker / HandResult / Hand / Landmark all line up).
 *
 * The webcam demo uses this directly (see ../src/main.ts); example projects
 * under ../examples/ reuse it too.
 *
 * Run it like this:
 *
 *   const tracker = new HandTracker({ maxHands: 2 });
 *   await tracker.initialize();            // downloads the .task model once
 *   const result = tracker.detectForVideo(videoEl);
 *   for (const hand of result.hands) { ... }
 *   tracker.close();
 *
 * The mirrored-camera quirk (same one that trips people up in Python):
 * MediaPipe determines handedness *assuming the input image is mirrored*
 * (a selfie-style feed). An <video> element playing getUserMedia output is
 * NOT mirrored, so this wrapper's `mirrored` option defaults to `false`
 * (meaning: swap MediaPipe's labels to get the physical hand). If you feed it
 * a mirrored canvas/video source instead, pass `mirrored: true`.
 */

import {
  FilesetResolver,
  HandLandmarker,
  type HandLandmarkerResult,
} from "@mediapipe/tasks-vision";
import { LandmarkSmoother, type SmoothingOptions } from "./smoothing";

/** One 3D landmark, normalized to [0, 1] (matches the Python `Landmark`). */
export interface Landmark {
  x: number;
  y: number;
  z: number;
}

/** A detected hand with its 21 landmarks (matches the Python `Hand`). */
export interface Hand {
  landmarks: Landmark[];
  handedness: "Left" | "Right";
  confidence: number;
  worldLandmarks?: Landmark[] | null;
}

/** Clean result of one frame (matches the Python `HandResult`). */
export class HandResult {
  hands: Hand[];
  timestampMs: number;

  constructor(hands: Hand[], timestampMs: number) {
    this.hands = hands;
    this.timestampMs = timestampMs;
  }

  get isEmpty(): boolean {
    return this.hands.length === 0;
  }
}

export interface HandTrackerOptions {
  /** Maximum hands per frame: 1 or 2. Default 2. */
  maxHands?: 1 | 2;
  /** Min confidence for hand detection. Default 0.5. */
  minDetectionConfidence?: number;
  /** Min confidence for tracking an already-detected hand. Default 0.5. */
  minTrackingConfidence?: number;
  /**
   * Whether input pixels are selfie-mirrored. Default `false` because
   * HTMLVideoElement frames are unmirrored. See class docstring.
   */
  mirrored?: boolean;
  /** Override the .task model URL. */
  modelUrl?: string;
  /**
   * Apply one-euro landmark smoothing before returning results.
   * `true` (default) uses sensible defaults; pass an object to tune it,
   * or `false` to disable (raw MediaPipe output jitters).
   */
  smoothing?: boolean | SmoothingOptions;
}

/** Official float16 Hand Landmarker model from Google's MediaPipe model zoo. */
export const DEFAULT_MODEL_URL =
  "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task";

function swapHandedness(label: string): "Left" | "Right" {
  return label === "Left" ? "Right" : "Left";
}

export class HandTracker {
  private landmarker: HandLandmarker | null = null;
  private readonly opts: Required<HandTrackerOptions>;
  private smoother: LandmarkSmoother | null;

  constructor(options: HandTrackerOptions = {}) {
    this.opts = {
      maxHands: options.maxHands ?? 2,
      minDetectionConfidence: options.minDetectionConfidence ?? 0.5,
      minTrackingConfidence: options.minTrackingConfidence ?? 0.5,
      mirrored: options.mirrored ?? false,
      modelUrl: options.modelUrl ?? DEFAULT_MODEL_URL,
      smoothing: options.smoothing ?? true,
    };
    this.smoother = this.opts.smoothing ? new LandmarkSmoother(this.opts.smoothing === true ? {} : this.opts.smoothing) : null;
  }

  /** Download/load the model and create the underlying HandLandmarker. */
  async initialize(): Promise<void> {
    if (this.landmarker) return;

    const wasmLoader = await FilesetResolver.forVisionTasks(
      "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm",
    );

    this.landmarker = await HandLandmarker.createFromOptions(wasmLoader, {
      baseOptions: {
        modelAssetPath: this.opts.modelUrl,
        delegate: "GPU",
      },
      runningMode: "VIDEO",
      numHands: this.opts.maxHands,
      minHandDetectionConfidence: this.opts.minDetectionConfidence,
      minHandPresenceConfidence: this.opts.minTrackingConfidence,
      minTrackingConfidence: this.opts.minTrackingConfidence,
    });
  }

  /**
   * Run hand tracking on one video frame.
   *
   * @param video A playing <video> element (from getUserMedia or an <input>).
   * @returns A HandResult. No hand in frame -> an empty result, never an error.
   */
  detectForVideo(video: HTMLVideoElement): HandResult {
    if (!this.landmarker) {
      throw new Error("HandTracker not initialized — call await initialize() first.");
    }
    const timestampMs = performance.now();
    const raw = this.landmarker.detectForVideo(video, timestampMs);
    const result = toHandResult(raw, this.opts.mirrored, timestampMs);
    if (this.smoother) {
      result.hands = this.smoother.update(result.hands);
    }
    return result;
  }

  /** Release the underlying landmarker. Safe to call more than once. */
  close(): void {
    this.landmarker?.close();
    this.landmarker = null;
    this.smoother = null;
  }
}

/** Convert MediaPipe's raw result into OpenHandTrack's clean result. */
export function toHandResult(
  raw: HandLandmarkerResult,
  mirrored: boolean,
  timestampMs: number,
): HandResult {
  const hands: Hand[] = [];

  for (let i = 0; i < raw.landmarks.length; i++) {
    const landmarks: Landmark[] = raw.landmarks[i].map((lm) => ({
      x: lm.x,
      y: lm.y,
      z: lm.z,
    }));

    const category = raw.handedness[i]?.[0];
    let handedness = (category?.categoryName ?? "Right") as "Left" | "Right";
    const confidence = category?.score ?? 0;
    if (!mirrored) {
      handedness = swapHandedness(handedness);
    }

    const world = raw.worldLandmarks?.[i]?.map((lm) => ({ x: lm.x, y: lm.y, z: lm.z })) ?? null;

    hands.push({ landmarks, handedness, confidence, worldLandmarks: world });
  }

  return new HandResult(hands, timestampMs);
}
