# Getting Started

## Python

### Install

```bash
pip install openhandtrack
```

Or with example dependencies:

```bash
pip install "openhandtrack[examples]"
```

Requires Python 3.11+. The `mediapipe` wheel pulls in `numpy` and `opencv-python` automatically.

### Hello World

```python
import cv2
from openhandtrack import HandTracker

cap = cv2.VideoCapture(0)
with HandTracker() as tracker:
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        result = tracker.process(frame)
        print(f"{len(result)} hand(s)", *(h.handedness for h in result))
        cv2.imshow("tracking", frame)
        if cv2.waitKey(1) == ord("q"):
            break
cap.release()
```

The model auto-downloads on first run (~7 MB) and is cached locally.

### Key Concepts

- **HandTracker** — the main class. Supports `VIDEO` and `LIVE_STREAM` running modes.
- **HandResult** — contains `.hands` (list of `Hand` objects), is iterable and truthy when hands are present.
- **Hand** — `.landmarks` (21 `Landmark` objects), `.handedness` (`"Left"` or `"Right"`), `.confidence`.
- **LandmarkSmoother** — optional One-Euro filtering for jitter-free tracking.

## Web

### Install

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:5173`, allow camera access, and hold up your hand.

### Try the Live Demo

No install needed — works from any browser including mobile:

**[xznder1984.github.io/OpenHandTracker](https://xznder1984.github.io/OpenHandTracker/)**

### Key Concepts

- **HandTracker** — TypeScript wrapper around `HandLandmarker`, mirrors the Python API shape.
- **One-Euro Smoothing** — built-in, enabled by default.
- **Canvas Renderer** — draws the hand skeleton with color-coded left (cyan) vs right (orange).

```ts
import { HandTracker } from "./tracker";

const tracker = new HandTracker({ maxHands: 2, mirrored: true });
await tracker.initialize();

// in your animation loop:
const result = tracker.detectForVideo(videoElement);
for (const hand of result.hands) {
  const tip = hand.landmarks[8]; // index fingertip
  console.log(hand.handedness, hand.confidence, tip.x, tip.y);
}
```

## The Mirrored-Camera Quirk

MediaPipe labels handedness **assuming the input image is mirrored** (selfie-style). The web demo CSS mirrors the video, so MediaPipe's raw labels are already correct. If you process unmirrored frames, pass `mirrored: false` to swap the labels for you.

See the [API Reference](/api-reference) for full details.
