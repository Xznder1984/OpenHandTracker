/**
 * Canvas skeleton rendering for the webcam demo.
 *
 * Draws the 21 hand landmarks connected by the real hand bone structure
 * (thumb chain, four finger chains, and the palm edges), color-coded per
 * hand (cyan = left, orange = right) so two hands don't blend together.
 *
 * Coordinates from the tracker are normalized to [0, 1]; they're scaled to
 * the canvas in drawHandResult.
 */

import { HandLandmarker } from "@mediapipe/tasks-vision";
import type { Hand, HandResult, Landmark } from "./tracker";

const FALLBACK_HAND_CONNECTIONS: readonly (readonly [number, number])[] = [
  // Thumb
  [0, 1], [1, 2], [2, 3], [3, 4],
  // Index finger
  [0, 5], [5, 6], [6, 7], [7, 8],
  // Middle finger
  [5, 9], [9, 10], [10, 11], [11, 12],
  // Ring finger
  [9, 13], [13, 14], [14, 15], [15, 16],
  // Pinky
  [13, 17], [17, 18], [18, 19], [19, 20],
  // Palm
  [0, 17],
];

/** MediaPipe's canonical hand bone connections, with a readable fallback. */
export const HAND_CONNECTIONS: readonly (readonly [number, number])[] =
  (HandLandmarker.HAND_CONNECTIONS ?? FALLBACK_HAND_CONNECTIONS).map((c) => [c.start, c.end]);

export interface DrawOptions {
  /** Color per hand label. */
  colors?: { Left: string; Right: string };
  /** Stroke width of bone lines, in canvas pixels. Default 3. */
  lineWidth?: number;
  /** Radius of the landmark dots, in canvas pixels. Default 4. */
  dotRadius?: number;
  /** Show the handedness label near the wrist. Default true. */
  showLabels?: boolean;
  /** Show landmark dots (in addition to bones). Default true. */
  showLandmarks?: boolean;
}

const DEFAULT_COLORS = { Left: "#22d3ee", Right: "#fb923c" };

/** True when a normalized landmark is actually inside the frame. */
function inFrame(lm: Landmark): boolean {
  return lm.x >= 0 && lm.x <= 1 && lm.y >= 0 && lm.y <= 1;
}

/**
 * Draw one hand's skeleton onto a canvas.
 *
 * @param ctx Canvas 2D context (already sized to the video frame).
 * @param hand The hand to draw.
 * @param options Tuning.
 */
export function drawHand(ctx: CanvasRenderingContext2D, hand: Hand, options: DrawOptions = {}): void {
  const colors = options.colors ?? DEFAULT_COLORS;
  const lineWidth = options.lineWidth ?? 3;
  const dotRadius = options.dotRadius ?? 4;
  const showLabels = options.showLabels ?? true;
  const showLandmarks = options.showLandmarks ?? true;
  const width = ctx.canvas.width;
  const height = ctx.canvas.height;

  const color = colors[hand.handedness] ?? DEFAULT_COLORS.Right;
  const toPx = (lm: Landmark): [number, number] => [lm.x * width, lm.y * height];

  // Bones
  ctx.strokeStyle = color;
  ctx.lineWidth = lineWidth;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.beginPath();
  for (const [a, b] of HAND_CONNECTIONS) {
    const pa = hand.landmarks[a];
    const pb = hand.landmarks[b];
    if (!inFrame(pa) || !inFrame(pb)) continue;
    const [ax, ay] = toPx(pa);
    const [bx, by] = toPx(pb);
    ctx.moveTo(ax, ay);
    ctx.lineTo(bx, by);
  }
  ctx.stroke();

  // Landmark dots
  if (showLandmarks) {
    ctx.fillStyle = color;
    ctx.beginPath();
    for (const lm of hand.landmarks) {
      if (!inFrame(lm)) continue;
      const [x, y] = toPx(lm);
      ctx.moveTo(x + dotRadius, y);
      ctx.arc(x, y, dotRadius, 0, Math.PI * 2);
    }
    ctx.fill();
  }

  // Handedness label next to the wrist
  if (showLabels && hand.landmarks[0] && inFrame(hand.landmarks[0])) {
    const [x, y] = toPx(hand.landmarks[0]);
    ctx.font = "600 14px system-ui, sans-serif";
    ctx.textBaseline = "bottom";
    const text = `${hand.handedness} ${Math.round(hand.confidence * 100)}%`;
    ctx.fillStyle = "rgba(15, 23, 42, 0.72)";
    const pad = 4;
    const tw = ctx.measureText(text).width;
    ctx.fillRect(x - tw / 2 - pad, y + 8, tw + pad * 2, 18);
    ctx.fillStyle = color;
    ctx.fillText(text, x - tw / 2, y + 24);
  }
}

/**
 * Draw the video frame plus all tracked hands' skeletons.
 * Call this once per animation frame.
 *
 * @param ctx Canvas 2D context sized to the video.
 * @param video The live video element (drawn as the background).
 * @param result Tracker result for the current frame.
 * @param options Tuning (forwarded to drawHand).
 */
export function drawHandResult(
  ctx: CanvasRenderingContext2D,
  video: HTMLVideoElement,
  result: HandResult,
  options: DrawOptions = {},
): void {
  const { width, height } = ctx.canvas;
  ctx.drawImage(video, 0, 0, width, height);
  for (const hand of result.hands) {
    drawHand(ctx, hand, options);
  }
}
