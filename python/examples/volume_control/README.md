# Gesture Volume Control 🔊

Spread your thumb and index finger apart to turn the volume up; pinch them
together to turn it down. No touching anything.

## Run

```bash
# from the repo root (once)
python -m venv .venv && .venv/bin/pip install -e "python/[examples]"

# then
.venv/bin/python python/examples/volume_control/volume_control.py
```

## Platform support

| Platform | Backend | Notes |
|----------|---------|-------|
| Windows | `pycaw` | installed automatically via `pip install -e "python/[examples]"` |
| macOS | AppleScript (`osascript`) | no extra deps |
| Linux | `pactl` → `amixer` | uses whatever is installed |
| Any other / no tooling | mock | prints volume, gesture code still runs |

If the real backend can't be reached (missing deps, no audio server, missing
permissions), the example falls back to the mock with a printed note — so the
gesture logic is testable everywhere.

## How it works

`gestures.pinch_distance(hand)` returns the thumb↔index gap normalized by hand
size (so camera distance doesn't matter). That value is mapped across
`MIN_PINCH..MAX_PINCH` onto `0..1` volume, smoothed with an EMA to hide pinch
jitter, and pushed to the platform backend.
