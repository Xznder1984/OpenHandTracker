# Landmarks

MediaPipe's Hand Landmarker returns **21 landmarks per hand**, always in the
same order, normalized to `[0, 1]` relative to the frame.

## Coordinate System

- **`x`** — horizontal position (0 = left edge, 1 = right edge)
- **`y`** — vertical position (0 = top, 1 = bottom)
- **`z`** — depth; roughly the *negative* distance from the camera in the
  same normalized units (fingertips closer to the camera are more negative)

## Landmark Table

| Index | Name | Joint | Notes |
|-------|------|-------|-------|
| 0 | `WRIST` | wrist | Hand anchor. Used to normalize pinch distance. |
| 1 | `THUMB_CMC` | thumb base | Carpometacarpal joint. |
| 2 | `THUMB_MCP` | thumb knuckle | Metacarpophalangeal joint. |
| 3 | `THUMB_IP` | thumb middle | Interphalangeal joint. |
| 4 | `THUMB_TIP` | thumb tip | Pinch with index tip (landmark 8). |
| 5 | `INDEX_MCP` | index knuckle | Base of index finger. |
| 6 | `INDEX_PIP` | index middle | Proximal interphalangeal. |
| 7 | `INDEX_DIP` | index tip joint | Distal interphalangeal. |
| 8 | `INDEX_TIP` | index fingertip | Most-used landmark — pointing, pressing, pinch. |
| 9 | `MIDDLE_MCP` | middle knuckle | With wrist, defines hand scale for pinch_distance. |
| 10 | `MIDDLE_PIP` | middle middle | |
| 11 | `MIDDLE_DIP` | middle tip joint | |
| 12 | `MIDDLE_TIP` | middle fingertip | |
| 13 | `RING_MCP` | ring knuckle | |
| 14 | `RING_PIP` | ring middle | |
| 15 | `RING_DIP` | ring tip joint | |
| 16 | `RING_TIP` | ring fingertip | |
| 17 | `PINKY_MCP` | pinky knuckle | Connected to wrist in the bone layout. |
| 18 | `PINKY_PIP` | pinky middle | |
| 19 | `PINKY_DIP` | pinky tip joint | |
| 20 | `PINKY_TIP` | pinky fingertip | |

## Bone Connections

These index pairs form the hand skeleton:

```
thumb   0–1  1–2  2–3  3–4
index   0–5  5–6  6–7  7–8
middle  5–9  9–10 10–11 11–12
ring    9–13 13–14 14–15 15–16
pinky   13–17 17–18 18–19 19–20
palm    0–17
```

## Visual Reference

```
       4     8     12    16    20          ← tips
       |     |     |     |     |
       3     7     11    15    19          ← DIP
       |     |     |     |     |
       2     6     10    14    18          ← PIP
       |     |     |     |     |
       1     5      9    13    17          ← MCP / CMC
        \    |      |     |    /
         \   |      0    |   /             ← 0 = wrist
          \  |      |    |  /
           \_________/    (pinky attaches at wrist too)

  thumb  index middle ring pinky
```

## Tips

- Fingers **curl** around their PIP: a curled fingertip folds back toward the
  palm, so it ends up close to both the wrist and its own knuckle.
  `count_extended_fingers()` checks both distances and only counts the finger
  as extended when both agree — that keeps counts stable on tilted hands.
- Landmarks can land slightly outside `[0, 1]` when a joint is occluded.
- `world_landmarks` gives the same 21 points in meters relative to the hand.

## Python Usage

```python
from openhandtrack import gestures as g

index_tip = hand.landmarks[g.INDEX_TIP]  # 8
wrist = hand.landmarks[g.WRIST]          # 0
pinch_gap = g.pinch_distance(hand)       # uses 4 & 8, normalized by 0–9
```
