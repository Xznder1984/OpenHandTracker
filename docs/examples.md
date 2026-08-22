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

### Volume Control

Thumb/index spread controls system volume. Works on macOS (osascript), Windows (pycaw), and Linux (pactl). Falls back to a mock for testing without audio hardware.

```bash
cd python/examples/volume_control
python volume_control.py
```

| Gesture | Action |
|---------|--------|
| Spread thumb + index | Increase volume |
| Pinch thumb + index | Decrease volume |

### Presentation Remote

Swipe gestures send arrow keys for slide navigation. Uses pynput (with mock fallback).

```bash
cd python/examples/presentation_remote
python presentation_remote.py
```

| Gesture | Action |
|---------|--------|
| Swipe right | Next slide |
| Swipe left | Previous slide |

## Web Examples

### Virtual Piano

Fingertip tracking + pinch detection triggers piano notes via Web Audio. Each finger maps to a key.

```bash
cd web/examples/virtual-piano
npm install
npm run dev
```

| Gesture | Action |
|---------|--------|
| Fingertip down | Press key |
| Pinch | Sustain note |

## Adding Your Own

See [Contributing](/contributing) for how to add a new example to the project.
