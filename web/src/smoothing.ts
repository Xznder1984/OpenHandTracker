/**
 * One-Euro landmark smoothing for the browser — a TypeScript port of the
 * 1€ filter used on the Python side (Casiez et al., CHI 2012).
 *
 * Raw MediaPipe output jitters a few pixels per frame; this is what makes the
 * skeleton look "glued on" instead of twitchy. The 1€ filter raises its
 * smoothing cutoff as the signal speeds up, so it stays responsive to fast
 * movement while removing slow jitter.
 */

/** One-Euro filter parameters (see LandmarkSmoother docs for tuning). */
export interface SmoothingOptions {
  minCutoff?: number;
  beta?: number;
  dCutoff?: number;
  /** Consecutive frames a hand may be absent before its filters reset. */
  resetAfterFrames?: number;
}

/** One smoothing filter for a single scalar signal. */
class OneEuroFilter {
  private minCutoff: number;
  private beta: number;
  private dCutoff: number;
  private xPrev: number | null = null;
  private dxPrev = 0;
  private tPrev: number | null = null;

  constructor(minCutoff = 1.0, beta = 0.007, dCutoff = 1.0) {
    this.minCutoff = minCutoff;
    this.beta = beta;
    this.dCutoff = dCutoff;
  }

  private alpha(cutoff: number, dt: number): number {
    const tau = 1 / (2 * Math.PI * cutoff);
    return dt > 0 ? 1 / (1 + tau / dt) : 1;
  }

  apply(value: number, timestamp: number): number {
    if (this.tPrev === null) {
      this.reset();
      this.tPrev = timestamp;
      this.xPrev = value;
      return value;
    }
    const dt = Math.max(timestamp - this.tPrev, 1e-4);
    this.tPrev = timestamp;

    const dx = (value - (this.xPrev as number)) / dt;
    const dxSmooth =
      this.alpha(this.dCutoff, dt) * dx + (1 - this.alpha(this.dCutoff, dt)) * this.dxPrev;
    this.dxPrev = dxSmooth;

    const cutoff = this.minCutoff + this.beta * Math.abs(dxSmooth);
    const smoothed = this.alpha(cutoff, dt) * value + (1 - this.alpha(cutoff, dt)) * (this.xPrev as number);
    this.xPrev = smoothed;
    return smoothed;
  }

  reset(): void {
    this.xPrev = null;
    this.dxPrev = 0;
    this.tPrev = null;
  }
}

/** Smoothes all 21 landmarks per hand across frames. */
export class LandmarkSmoother {
  private minCutoff: number;
  private beta: number;
  private dCutoff: number;
  private resetAfterFrames: number;
  private filters = new Map<string, OneEuroFilter[][][]>(); // label -> [hand][landmark][x,y,z]
  private missing = new Map<string, number>();

  constructor(options: SmoothingOptions = {}) {
    this.minCutoff = options.minCutoff ?? 1.0;
    this.beta = options.beta ?? 0.007;
    this.dCutoff = options.dCutoff ?? 1.0;
    this.resetAfterFrames = options.resetAfterFrames ?? 15;
  }

  private filtersFor(label: string): OneEuroFilter[][][] {
    let bank = this.filters.get(label);
    if (!bank) {
      bank = Array.from({ length: 2 }, () =>
        Array.from({ length: 21 }, () => [
          new OneEuroFilter(this.minCutoff, this.beta, this.dCutoff),
          new OneEuroFilter(this.minCutoff, this.beta, this.dCutoff),
          new OneEuroFilter(this.minCutoff, this.beta, this.dCutoff),
        ]),
      );
      this.filters.set(label, bank);
    }
    return bank;
  }

  /**
   * Smooth one frame's hands. Hands are keyed by handedness label so a hand
   * keeps its filter history even when detection order changes.
   */
  update<T extends { handedness: string; landmarks: { x: number; y: number; z: number }[] }>(
    hands: T[],
    timestamp = performance.now(),
  ): T[] {
    const seen = new Set<string>();
    const slotsUsed = new Map<string, number>();
    const smoothed: T[] = [];

    for (const hand of hands) {
      const label = hand.handedness;
      const slot = slotsUsed.get(label) ?? 0;
      slotsUsed.set(label, slot + 1);
      seen.add(label);

      const bank = this.filtersFor(label)[slot];
      const newLandmarks = hand.landmarks.map((lm, i) => {
        const [fx, fy, fz] = bank[i];
        return { x: fx.apply(lm.x, timestamp), y: fy.apply(lm.y, timestamp), z: fz.apply(lm.z, timestamp) };
      });
      smoothed.push({ ...hand, landmarks: newLandmarks });
    }

    for (const label of this.filters.keys()) {
      this.missing.set(label, seen.has(label) ? 0 : (this.missing.get(label) ?? 0) + 1);
    }
    for (const [label, missed] of [...this.missing.entries()]) {
      if (missed > this.resetAfterFrames) {
        this.filters.delete(label);
        this.missing.delete(label);
      }
    }
    return smoothed;
  }

  /** Drop all filter history (e.g. when switching camera sources). */
  reset(): void {
    this.filters.clear();
    this.missing.clear();
  }
}
