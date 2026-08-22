# Air Draw ✏️

Pinch to draw in the air, open your palm to lift the "pen", hold a fist for
one second to clear the canvas. A dwell-based palette at the top of the
screen lets you pick between 7 colours and an eraser with your fingertip.

The whole gesture logic is a few calls into `openhandtrack.gestures` on top
of one `HandTracker` — that's the point of the library.

## Run

```bash
# from the repo root (once)
python3.12 -m venv .venv && .venv/bin/pip install -e "python/[examples]"

# then
.venv/bin/python python/examples/air_draw/air_draw.py
```

## Controls

| Gesture | Action |
|---------|--------|
| Pinch (thumb + index) | Pen down — draw (or erase, if eraser is selected) |
| Open palm | Pen up — move without drawing |
| Fist held ~1 s | Clear canvas |
| Hover fingertip over a swatch ~0.6 s | Pick colour / eraser |
| Keys `1`-`7`, `e` | Pick colour directly / eraser (handy fallback) |
| `q` | Quit |

Landmarks are smoothed with `LandmarkSmoother` so the ink line is smooth
instead of twitchy.

## How it works

1. `HandTracker.process(frame)` → clean `HandResult` each frame.
2. `LandmarkSmoother.update(...)` smooths the 21 points.
3. `gestures.is_pinch / is_open_palm / is_fist` decide pen state.
4. The palette is plain rectangles: hit-test the smoothed index tip against
   them, hold still to fill the progress bar, then the swatch activates.
   Strokes are suppressed while the fingertip is inside the palette strip.
5. Erasing is just drawing black strokes onto the off-screen canvas — black
   is transparent in the video composite, so it looks like a real eraser.
6. `cv2.line` inks onto an off-screen canvas composited over the video.
