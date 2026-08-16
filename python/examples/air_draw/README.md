# Air Draw ✏️

Pinch to draw in the air, open your palm to lift the "pen", hold a fist for
one second to clear the canvas.

The whole gesture logic is a few calls into `openhandtrack.gestures` on top
of one `HandTracker` — that's the point of the library.

## Run

```bash
# from the repo root (once)
python -m venv .venv && .venv/bin/pip install -e "python/[examples]"

# then
.venv/bin/python python/examples/air_draw/air_draw.py
```

## Controls

| Gesture | Action |
|---------|--------|
| Pinch (thumb + index) | Pen down — draw |
| Open palm | Pen up — move without drawing |
| Fist held ~1 s | Clear canvas |
| `q` | Quit |

Landmarks are smoothed with `LandmarkSmoother` so the ink line is smooth
instead of twitchy.

## How it works

1. `HandTracker.process(frame)` → clean `HandResult` each frame.
2. `LandmarkSmoother.update(...)` smooths the 21 points.
3. `gestures.is_pinch / is_open_palm / is_fist` decide pen state.
4. `cv2.line` inks onto an off-screen canvas composited over the video.
