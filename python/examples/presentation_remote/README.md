# Presentation Remote 🖥️

Swipe your hand to advance your slides — no clicker needed. Works with
PowerPoint, Google Slides, Keynote, and anything else that answers to the
arrow keys.

## Run

```bash
# from the repo root (once)
python -m venv .venv && .venv/bin/pip install -e "python/[examples]"

# then
.venv/bin/python python/examples/presentation_remote/presentation_remote.py
```

## Controls

| Gesture | Action |
|---------|--------|
| Hand swipes right (fast) | Next slide → `Right` arrow |
| Hand swipes left (fast) | Previous slide → `Left` arrow |
| `q` | Quit |

## Platform support

- **Key presses**: `pynput` (cross-platform). On macOS the process may need
  Accessibility permission the first time.
- **No keyboard control available** (headless, permission denied): the example
  prints the would-be keystroke — the swipe logic still runs and is testable.

## How it works

The index fingertip's screen-space x is tracked over a ~250 ms sliding window.
If it moves past a velocity threshold (in normalized units/second), a swipe is
registered. A 0.6 s debounce stops a single swipe from firing twice, and
`LandmarkSmoother` keeps the trajectory stable enough that casual hand motion
doesn't trigger false swipes.
