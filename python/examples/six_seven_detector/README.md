# 6-7 Detector 📸🧠

A completely serious computer-vision application that watches your hand and
alerts you the instant you exhibit **six or seven** extended fingers.

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
| Show 6 or 7 fingers | MEME DETECTED — rainbow alert + counter++ |
| Anything else | Be humble |
| `q` | Quit (sit) |

Uses `gestures.count_extended_fingers` — that's genuinely the whole detection
logic, which is the joke.
