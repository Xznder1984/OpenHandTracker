# 6-7 Detector 📸🧠

A completely serious computer-vision application that watches both of your hands and
alerts you the instant their combined finger count hits **six or seven**.

Rainbow alert border, giant SIX SEVEN text, a persistent 67 counter, and a
terminal bell. Science.

## Run

```bash
# from the repo root
.venv/bin/python python/examples/six_seven_detector/six_seven_detector.py
```

## Controls

| Gesture | Action |
|---------|--------|
| Show 6 or 7 fingers across both hands | MEME DETECTED — rainbow alert + counter++ |
| Anything else | Be humble |
| `q` | Quit (sit) |

Sums `gestures.count_extended_fingers` over both hands — that's genuinely the whole detection
logic, which is the joke.
