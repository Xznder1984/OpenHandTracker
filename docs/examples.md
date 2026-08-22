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
