# Examples

Short, readable projects that show how little code a hand-tracking app needs.

## Python Examples

### Air Draw

Pinch to draw in the air, open palm to lift the pen, fist to clear the canvas.
Hover your fingertip over the palette at the top to switch colours or grab the eraser.

```bash
cd python/examples/air_draw
python air_draw.py
```

| Gesture | Action |
|---------|--------|
| Pinch (thumb + index) | Draw |
| Open palm | Lift pen |
| Fist | Clear canvas |
| Hover a swatch ~0.6s | Pick colour / eraser |
| Keys 1-7 / e | Pick colour directly / eraser |

### Finger Counter

Counts extended fingers and dots each fingertip green. The simplest example in the repo — start reading here.

| Gesture | Action |
|---------|--------|
| Show hand | Big number = extended finger count |

### Peace Selfie

Hold the peace sign (index + middle up) to arm a 3-second countdown, then a white flash saves `selfie_N.png` next to where you ran it.

| Gesture | Action |
|---------|--------|
| Hold ✌ ~3s | Countdown → photo saved |
| Anything else | Cancels countdown |

### Virtual Mouse

The smoothed index fingertip drives the OS cursor; pinch holds the left button (drag), release clicks. An open palm pauses control so you can reposition safely.

| Gesture | Action |
|---------|--------|
| Move index finger | Cursor follows |
| Pinch / release | Left button hold / click |
| Open palm | Pause cursor control |

### Air Scroll

Point above or below the frame's midline to scroll — speed scales with distance. Fist locks position for reading.

| Gesture | Action |
|---------|--------|
| Point up / down | Scroll up / down |
| Fist | Lock scrolling |
| Open palm | Stop |

### Pinch Ruler

Live meter of the normalized thumb↔index distance (`gestures.pinch_distance`) with the `is_pinch` threshold highlighted. Great for understanding why distances are divided by hand size.

### Two-Hand Zoom

Spread both hands apart to zoom in, squeeze to zoom out (Ctrl+scroll under the hood). Demonstrates `max_hands=2` and correlating two hands against a captured baseline.

| Gesture | Action |
|---------|--------|
| Show both hands | Capture baseline |
| Spread / squeeze | Zoom in / out |
| Hide one hand | Reset baseline |

### 6-7 Detector

Watches up to **both hands** and triggers a rainbow alert the instant the total
hits **six or seven** extended fingers. Persistent 67 counter, terminal bell,
zero scientific value. Uses `gestures.count_extended_fingers` summed across
hands — which is the whole detection logic, and the joke.

| Gesture | Action |
|---------|--------|
| Show 6 or 7 fingers across both hands | MEME DETECTED — rainbow alert + counter |
| `q` | Quit (sit) |
