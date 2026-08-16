# OpenHandTrack — Python

Real-time 3D hand tracking for Python, wrapping MediaPipe's **Hand Landmarker**
task behind a small, clean API — no fighting `mediapipe.tasks` internals.

- **21 landmarks** per hand (x, y, z), up to **2 hands**
- **Handedness** with confidence, mirrored-camera quirk handled for you
- **Gesture helpers** (`is_fist`, `is_open_palm`, `is_pinch`, …)
- **One-Euro smoothing** so the tracking feels solid instead of twitchy
- Auto-downloads the model on first use (cached locally, not in git)
- Works on **macOS, Windows, Linux** — pure stdlib for model download

## Install

```bash
python -m venv .venv
.venv/bin/pip install -e "python/[examples]"   # library + example deps
```

Requires Python 3.11+. The `mediapipe` wheel pulls in `numpy` + `opencv-python`
automatically.

## Hello world

```python
import cv2
from openhandtrack import HandTracker

cap = cv2.VideoCapture(0)
with HandTracker() as tracker:            # model auto-downloads on first run
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        result = tracker.process(frame)   # BGR frame in, clean result out
        print(f"{len(result)} hand(s)", *(h.handedness for h in result))
        cv2.imshow("tracking", frame)
        if cv2.waitKey(1) == ord("q"):
            break
cap.release()
```

`result.hands` is empty (never an error) when no hand is in frame.

## API at a glance

| Symbol | What it is |
|--------|------------|
| `HandTracker(max_hands, min_detection_confidence, min_tracking_confidence, running_mode, mirrored)` | The main class. Context manager; `running_mode` supports `"VIDEO"` and `"LIVE_STREAM"`. |
| `HandTracker.process(frame) -> HandResult` | Track one BGR numpy frame. |
| `HandResult` | `.hands`, `len()`, `iter()`, truthy when a hand is present. |
| `Hand` | `.landmarks` (21×`Landmark`), `.handedness` (`"Left"`/`"Right"`), `.confidence`, `.world_landmarks`. |
| `Landmark` | `.x`, `.y`, `.z` in normalized units. |
| `LandmarkSmoother(num_hands, min_cutoff, beta, …)` | One-Euro smoothing across frames. `smoother.update(result.hands)` → smoothed hands. |
| `OneEuroFilter` / `ExponentialMovingAverage` | Raw filters, if you want them standalone. |
| `gestures.count_extended_fingers(hand)` | 0–5. |
| `gestures.is_fist(hand)` / `is_open_palm(hand)` | Boolean pose checks. |
| `gestures.is_pinch(hand, threshold)` | `(bool, distance)` — distance is useful for pinch-to-grab. |
| `gestures.pinch_distance(hand)` | Thumb↔index gap normalized by hand size. |
| `gestures.pointing_direction(hand)` | `(dx, dy)` unit vector of the index finger. |

Full docstrings live in the source (`openhandtrack/tracker.py`,
`smoothing.py`, `gestures.py`) — that's the reference.

### The mirrored-camera quirk

MediaPipe labels handedness **assuming the input image is mirrored** (a
selfie-style webcam feed). `HandTracker` defaults to `mirrored=True` to match
the common "mirror your webcam view" setup. If you process unmirrored frames
(rear camera, video files), pass `mirrored=False` and the labels are swapped
for you. Hold up your right hand: if it reports `Left`, flip the flag.

## Examples

Short, readable projects that reuse this library — see `examples/`:

- `air_draw/` — pinch to draw in the air, palm to lift, fist to clear.
- `volume_control/` — thumb/index spread controls system volume (with a
  platform-agnostic mock fallback).
- `presentation_remote/` — swipe gestures send arrow keys to your slides.

## Tests

```bash
.venv/bin/python -m pytest python/
```

## License

Apache-2.0 — same as MediaPipe, so you can build on it freely.
