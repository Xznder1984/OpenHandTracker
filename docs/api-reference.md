# API Reference

## Python (`openhandtrack`)

### HandTracker

```python
from openhandtrack import HandTracker

tracker = HandTracker(
    max_hands=2,                    # 1 or 2
    min_detection_confidence=0.5,   # hand detection threshold
    min_tracking_confidence=0.5,    # tracking confidence threshold
    running_mode="VIDEO",           # "VIDEO" or "LIVE_STREAM"
    mirrored=True,                  # True = selfie input, False = raw camera
)
```

| Method | Description |
|--------|-------------|
| `process(frame) -> HandResult` | Track one BGR numpy frame. Returns empty result when no hand is present. |
| `__enter__` / `__exit__` | Context manager that releases resources. |

### HandResult

| Property | Type | Description |
|----------|------|-------------|
| `hands` | `list[Hand]` | Detected hands (empty list if none). |

Supports `len()`, `iter()`, and truthiness (`if result:`).

### Hand

| Property | Type | Description |
|----------|------|-------------|
| `landmarks` | `list[Landmark]` | 21 normalized landmarks. |
| `handedness` | `str` | `"Left"` or `"Right"` (physical hand, not image side). |
| `confidence` | `float` | Handedness confidence (0–1). |
| `world_landmarks` | `list[Landmark] \| None` | 3D landmarks in meters (when available). |
| `palm_center` | `Landmark` | Average of wrist and middle-finger MCP. |

### Landmark

| Property | Type | Description |
|----------|------|-------------|
| `x` | `float` | Horizontal position (0 = left, 1 = right). |
| `y` | `float` | Vertical position (0 = top, 1 = bottom). |
| `z` | `float` | Depth (negative = closer to camera). |

### LandmarkSmoother

```python
from openhandtrack import LandmarkSmoother

smoother = LandmarkSmoother(
    num_hands=2,
    min_cutoff=1.0,   # lower = more smoothing
    beta=0.007,        # higher = more speed adaptation
)
smoothed_hands = smoother.update(result.hands)
```

### Gesture Helpers

| Function | Returns | Description |
|----------|---------|-------------|
| `is_fist(hand)` | `bool` | True when all fingers are curled. |
| `is_open_palm(hand)` | `bool` | True when all fingers are extended. |
| `is_pinch(hand, threshold=0.07)` | `(bool, float)` | Thumb-index proximity + distance. |
| `pinch_distance(hand)` | `float` | Normalized thumb-index gap (0 = touching). |
| `pointing_direction(hand)` | `(float, float)` | Unit vector `(dx, dy)` of index finger. |
| `count_extended_fingers(hand)` | `int` | 0–5 extended fingers. |

---

## Web (`src/tracker.ts`)

### HandTracker

```ts
const tracker = new HandTracker({
  maxHands: 2,                    // 1 or 2
  minDetectionConfidence: 0.5,
  minTrackingConfidence: 0.5,
  mirrored: true,                 // true = don't swap labels
  smoothing: true,                // or SmoothingOptions object
});
await tracker.initialize();       // loads model (~7 MB)
```

| Method | Description |
|--------|-------------|
| `detectForVideo(video) -> HandResult` | Track one frame from an `HTMLVideoElement`. |
| `close()` | Release the underlying landmarker. |

### HandResult

| Property | Type | Description |
|----------|------|-------------|
| `hands` | `Hand[]` | Detected hands. |
| `isEmpty` | `boolean` | True when no hands are present. |
| `timestampMs` | `number` | Frame timestamp. |

### Hand

| Property | Type | Description |
|----------|------|-------------|
| `landmarks` | `Landmark[]` | 21 normalized landmarks. |
| `handedness` | `"Left" \| "Right"` | Physical hand label. |
| `confidence` | `number` | Handedness confidence (0–1). |
| `worldLandmarks` | `Landmark[] \| null` | 3D landmarks in meters. |

### SmoothingOptions

```ts
{
  minCutoff: 1.0,   // lower = more smoothing
  beta: 0.007,       // higher = more speed adaptation
  dCutoff: 1.0,      // derivative cutoff
}
```

### Canvas Renderer

```ts
import { drawHandResult } from "./render";

drawHandResult(ctx, video, result, {
  showLabels: true,
  lineWidth: 3,
  dotRadius: 4,
  colors: { Left: "#22d3ee", Right: "#fb923c" },
});
```
