# Examples Guide

Ten hands-on apps you can run in under a minute — plus a browser demo.
Every example is a single short Python file, perfect for reading after you run it.

---

## Run any example in 3 steps

### One-time setup

**Easiest** — paste one line into your terminal:

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/Xznder1984/OpenHandTracker/main/tui.sh | bash
```

```powershell
# Windows (PowerShell)
irm https://raw.githubusercontent.com/Xznder1984/OpenHandTracker/main/tui.ps1 | iex
```

This clones the repo to `~/OpenHandTracker`, creates a virtual environment,
installs everything, and gives you a menu of all examples.

**Manual alternative:**

```bash
git clone https://github.com/Xznder1984/OpenHandTracker.git
cd OpenHandTracker
python3.12 -m venv .venv                 # 3.11 or 3.12 required
source .venv/bin/activate                # Windows: .venv\Scripts\activate
pip install -e "python[examples]"
```

> **Why 3.11/3.12 only?** MediaPipe (the engine underneath) ships wheels
> exclusively for those versions on desktop platforms.

### Every time

```bash
cd ~/OpenHandTracker                     # or wherever you cloned
source .venv/bin/activate                # Windows: .venv\Scripts\activate
python python/examples/<name>/<name>.py  # e.g. python/python/examples/finger_count/finger_count.py
```

### Good to know

- **`q` quits every example** (click the video window first if a keypress does nothing).
- **First run downloads the hand model (~6 MB)** into `~/.openhandtrack` — one time only.
- **Camera permission:** macOS asks once per terminal app — allow it
  (System Settings → Privacy & Security → Camera → enable your terminal).
- A window titled after the app opens showing your webcam + overlay. That's the app.

---

## The ten Python examples

| # | Example | One-liner | Difficulty to read |
|---|---------|-----------|--------------------|
| 1 | [Finger Counter](#finger-counter) | counts raised fingers | ★ start here |
| 2 | [Air Draw](#air-draw) | pinch to draw, palette + eraser | ★★ |
| 3 | [Peace Selfie](#peace-selfie) | ✌ → countdown → saved photo | ★ |
| 4 | [Virtual Mouse](#virtual-mouse) | finger steers your cursor | ★★★ |
| 5 | [Air Scroll](#air-scroll) | point up/down to scroll pages | ★★ |
| 6 | [Pinch Ruler](#pinch-ruler) | live thumb-index distance meter | ★ |
| 7 | [Two-Hand Zoom](#two-hand-zoom) | spread/squeeze both hands to zoom | ★★★ |
| 8 | [6-7 Detector](#6-7-detector) | rainbow brainrot alert | ★ |
| 9 | [Volume Control](#volume-control) | thumb-index spread = loudness | ★★ |
| 10 | [Presentation Remote](#presentation-remote) | swipe to change slides | ★★ |

### Finger Counter

`python python/examples/finger_count/finger_count.py`

Counts extended fingers and lights each fingertip green. The simplest example — read this one first to see the whole pipeline (capture → track → gesture → draw).

| Gesture | Action |
|---------|--------|
| Show your hand | Big number shows the count of extended fingers |

### Air Draw

`python python/examples/air_draw/air_draw.py`

Pinch to draw glowing lines in the air. A palette strip across the top lets you switch colours: hover your index fingertip over a swatch for ~0.6 s (a progress ring fills up) and it's selected.

| Gesture / Key | Action |
|---------------|--------|
| Pinch (thumb + index) | Draw |
| Open palm | Lift the pen (move without drawing) |
| Fist | Clear the whole canvas |
| Hover a swatch ~0.6 s | Pick colour / eraser |
| Keys `1`–`7` / `e` | Pick colour / eraser directly |

Tip: drawings persist until cleared — show someone your masterpiece before fisting it away.

### Peace Selfie

`python python/examples/peace_selfie/peace_selfie.py`

Hold a peace sign and a 3-second countdown starts; a white flash saves `selfie_N.png` into the folder where you launched it.

| Gesture | Action |
|---------|--------|
| Hold ✌ (index + middle up, others down) | Arms the 3-second countdown |
| Drop the pose mid-countdown | Cancels |

Photos land next to wherever you ran the command — not inside the repo clone of the app.

### Virtual Mouse

`python python/examples/virtual_mouse/virtual_mouse.py`

Your index fingertip becomes the cursor across your whole screen. Pinch = left button down (hold to drag), release = click. Requires the `pynput` extra (installed by default with `[examples]`). Accessibility permissions may be needed on macOS (System Settings → Privacy & Security → Accessibility → enable your terminal).

| Gesture | Action |
|---------|--------|
| Move index finger | Cursor follows (smoothed) |
| Pinch & hold | Left button down — drag |
| Release pinch | Click / drop |
| Open palm | Pause control so you can reposition |

Tip: the open-palm pause is your friend — palm whenever you need to re-lift your hand without the cursor flying.

### Air Scroll

`python python/examples/air_scroll/air_scroll.py`

Point your index finger above or below the frame's midline to scroll the focused window; scroll speed scales with distance from centre.

| Gesture | Action |
|---------|--------|
| Point above the midline | Scroll up |
| Point below the midline | Scroll down |
| Farther from centre | Faster scrolling |
| Fist | Lock position (read hands-free) |
| Open palm | Stop scrolling |

### Pinch Ruler

`python python/examples/pinch_ruler/pinch_ruler.py`

A live meter of the thumb↔index gap, normalised by your hand size so it reads the same at any distance from the camera. Includes the pinch-detection threshold line. Best example for understanding `gestures.pinch_distance`.

| Gesture | Action |
|---------|--------|
| Spread thumb & index | Meter rises |
| Touch them | Meter hits zero, PINCH indicator lights |

### Two-Hand Zoom

`python python/examples/two_hand_zoom/two_hand_zoom.py`

Zoom any zoomable surface (maps, browsers, PDFs) by spreading or squeezing both hands. Under the hood it sends Ctrl+scroll events — the same multi-hand baseline technique powers anything two-handed.

| Gesture | Action |
|---------|--------|
| Show both hands | Captures baseline distance |
| Spread hands apart | Zoom in |
| Squeeze together | Zoom out |
| Hide one hand | Resets baseline |

### 6-7 Detector

`python python/examples/six_seven_detector/six_seven_detector.py`

Watches **both hands** and sums their fingers. Hit a combined total of six or seven and… you'll see. Terminal bell included. Zero scientific value, maximum cultural relevance.

| Gesture | Action |
|---------|--------|
| 6 or 7 fingers across both hands | MEME DETECTED — rainbow alert + persistent counter |
| Anything else | Be humble |
| `q` | Quit (sit) |

### Volume Control

`python python/examples/volume_control/volume_control.py`

Your thumb↔index gap *is* the system volume: spread wider for louder, pinch closed near the bottom to mute-ish levels. Works via OS media APIs on macOS, Windows and Linux.

| Gesture | Action |
|---------|--------|
| Spread thumb ↔ index | Volume up (meter shows level) |
| Close them | Volume down |
| Hold ~1 s at minimum | Mute toggle |

Tip: open palm drops out of volume mode so accidental gestures don't blast your ears.

### Presentation Remote

`python python/examples/presentation_remote/presentation_remote.py`

Swipe left/right in the air to send ←/→ arrow keys — advance slides from across the room. A fist arms swipe mode so random hand movements don't skip your deck.

| Gesture | Action |
|---------|--------|
| Fist | Arm swipe mode |
| Swipe left (while armed) | Previous slide (←) |
| Swipe right (while armed) | Next slide (→) |
| Open palm | Disarm |

---

## Bonus: the web demo (TypeScript)

Same tracking engine compiled for the browser — no install, just Node 18+:

```bash
cd web
npm install
npm run dev        # opens http://localhost:5173
```

Includes a **Virtual Piano**: hover an index fingertip over keys and pinch to play notes via Web Audio. Your video never leaves your machine — all inference runs locally via MediaPipe WASM.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `No webcam found` | Close other apps using the camera (Zoom, Meet…), re-plug external cams |
| Window opens but black | Grant your terminal camera access (see top of guide), restart the example |
| Keypress `q` does nothing | Click the video window once so it has keyboard focus |
| `Requires Python >=3.11,<3.13` error | Recreate the venv with Python 3.11 or 3.12 |
| Cursor/keys do nothing (mouse/scroll/remote) | Grant Accessibility permission to your terminal, then restart it |
| Everything lags | Good news: examples already detect on alternate frames; try lowering other apps' load or use a 720p camera mode |

Want more? Each example folder has its own `README.md`, and
[`docs/api-reference.md`](api-reference.md) documents every helper used here.
