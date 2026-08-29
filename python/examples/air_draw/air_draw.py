"""Air Draw — pinch to draw in the air, open palm to lift the pen, fist to clear.

Controls
--------
* Pinch (thumb + index together) ..... pen down, draw
* Open palm .......................... pen up (move without drawing)
* Fist held for ~1 second ............ clear the canvas
* Hover fingertip over a swatch ...... pick colour / eraser (hold ~0.6s)
* Keys 1-7 ........................... pick a colour directly, "e" = eraser
* Press "q" .......................... quit

The entire gesture logic is a handful of calls into
``openhandtrack.gestures`` plus one :class:`HandTracker`; everything else is
the little dwell-based palette UI on top.
"""

import time

import cv2
import numpy as np

from openhandtrack import HandTracker, LandmarkSmoother
from openhandtrack import gestures as g
from openhandtrack.hud import help_bar, print_controls

WINDOW = "Air Draw — pinch: draw | palm: lift | fist 1s: clear | hover swatches | q: quit"
CLEAR_HOLD_SECONDS = 1.0
SELECT_HOLD_SECONDS = 0.6  # dwell time to activate a palette swatch
MAX_HANDS = 1  # the first hand found drives the pen

PEN_SIZE = 5
ERASER_SIZE = 30
PALETTE_MARGIN = 10
SWATCH_W, SWATCH_H, SWATCH_GAP = 54, 36, 8

# (BGR, name) — BGR because that's what OpenCV wants
COLORS = [
    ((0, 215, 255), "yellow"),
    ((255, 200, 0), "cyan"),
    ((80, 220, 100), "green"),
    ((230, 120, 255), "magenta"),
    ((60, 60, 240), "red"),
    ((255, 160, 40), "blue"),
    ((255, 255, 255), "white"),
]
ERASE_COLOR = (0, 0, 0)  # black strokes vanish against the composite

Rect = tuple[int, int, int, int]

INSTRUCTIONS = [
    "Pinch: draw",
    "Palm: lift",
    "Fist 1s: clear",
    "Hover swatch: pick colour/eraser",
]


def build_palette(width: int) -> list[Rect]:
    """Centered row of swatches across the top: one per colour + eraser."""
    n = len(COLORS) + 1
    total = n * SWATCH_W + (n - 1) * SWATCH_GAP
    x0 = max(PALETTE_MARGIN, (width - total) // 2)
    return [
        (
            x0 + i * (SWATCH_W + SWATCH_GAP),
            PALETTE_MARGIN,
            x0 + i * (SWATCH_W + SWATCH_GAP) + SWATCH_W,
            PALETTE_MARGIN + SWATCH_H,
        )
        for i in range(n)
    ]


def hit_swatch(rects: list[Rect], pt: tuple[int, int]) -> int | None:
    x, y = pt
    return next(
        (i for i, (x1, y1, x2, y2) in enumerate(rects) if x1 <= x <= x2 and y1 <= y <= y2), None
    )


def draw_palette(
    frame: np.ndarray,
    rects: list[Rect],
    color_idx: int,
    erasing: bool,
    hover: int | None,
    progress: float,
) -> None:
    for i, (x1, y1, x2, y2) in enumerate(rects):
        fill = COLORS[i][0] if i < len(COLORS) else (70, 70, 70)  # eraser: dark
        cv2.rectangle(frame, (x1, y1), (x2, y2), fill, -1)

        if i == len(COLORS):  # eraser icon: small white block
            cv2.rectangle(frame, (x1 + 16, y1 + 8), (x2 - 16, y2 - 14), (235, 235, 235), -1)
            cv2.putText(
                frame,
                "ER",
                (x1 + 17, y2 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.35,
                (30, 30, 30),
                1,
                cv2.LINE_AA,
            )

        selected = erasing if i == len(COLORS) else (i == color_idx and not erasing)
        border = (255, 255, 255) if selected else (40, 40, 40)
        cv2.rectangle(frame, (x1, y1), (x2, y2), border, 3 if selected else 1)

        if i == hover and progress < 1.0:  # dwell progress bar
            bar_w = int(SWATCH_W * max(0.0, min(progress, 1.0)))
            cv2.rectangle(frame, (x1 + 2, y2 - 6), (x1 + 2 + bar_w, y2 - 2), (255, 255, 255), -1)


def draw_hud(frame: np.ndarray, pen_down: bool, color_idx: int, erasing: bool) -> None:
    """Overlay the control legend and pen state on the video frame."""
    top = PALETTE_MARGIN + SWATCH_H + 26
    for i, line in enumerate(INSTRUCTIONS):
        cv2.putText(
            frame,
            line,
            (12, top + i * 22),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

    tool = f"eraser ({ERASER_SIZE}px)" if erasing else f"{COLORS[color_idx][1]} pen"
    state = f"PEN DOWN — {tool}" if pen_down else f"PEN UP — {tool}"
    state_color = (
        (200, 200, 200) if erasing else (COLORS[color_idx][0] if pen_down else (160, 160, 160))
    )
    cv2.putText(
        frame,
        state,
        (12, frame.shape[0] - 14),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        state_color,
        2,
        cv2.LINE_AA,
    )



CONTROLS = [
    ('pinch', 'draw'),
    ('open palm', 'lift pen'),
    ('fist', 'clear canvas'),
    ('hover swatch ~0.6s / keys 1-7,e', 'pick colour or eraser'),
    ('q', 'quit'),
]

def main() -> None:
    print_controls("Air Draw", CONTROLS)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise SystemExit("No webcam found. Connect a camera and try again.")

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))  # faster USB path
    cap.set(cv2.CAP_PROP_FPS, 30)

    with (
        HandTracker(max_hands=MAX_HANDS) as tracker,
        LandmarkSmoother(num_hands=MAX_HANDS) as smoother,
    ):
        canvas: np.ndarray | None = None
        prev_tip: tuple[int, int] | None = None
        pen_down = False
        fist_since: float | None = None
        last_clear = 0.0

        palette: list[Rect] | None = None
        color_idx = 0
        erasing = False
        hover: int | None = None
        dwell_start: float | None = None
        armed = True  # must leave a swatch before it can trigger again

        frame_idx = 0
        prev_hands = None
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)  # selfie view; matches mirrored=True default
            if canvas is None or canvas.shape[:2] != frame.shape[:2]:
                canvas = np.zeros_like(frame)
            if palette is None:
                palette = build_palette(frame.shape[1])
            ui_bottom = PALETTE_MARGIN + SWATCH_H

            # track every other frame, reuse landmarks between: the video
            # still renders at full camera rate, so motion looks smoother
            frame_idx += 1
            if prev_hands is None or frame_idx % 2 == 0:
                prev_hands = smoother.update(tracker.process(frame).hands)
            hands = prev_hands
            now = time.monotonic()

            if hands:
                hand = hands[0]
                tip = hand.landmarks[g.INDEX_TIP]
                tip_xy = (int(tip.x * frame.shape[1]), int(tip.y * frame.shape[0]))

                if g.is_fist(hand):
                    if fist_since is None:
                        fist_since = now
                    elif now - fist_since >= CLEAR_HOLD_SECONDS and now - last_clear > 0.5:
                        canvas[:] = 0  # clear the drawing
                        last_clear = now
                        fist_since = None
                else:
                    fist_since = None

                # --- palette dwell selection ---
                idx = hit_swatch(palette, tip_xy) if not g.is_fist(hand) else None
                if idx != hover:
                    hover, dwell_start = idx, now
                elif (
                    idx is not None
                    and armed
                    and dwell_start is not None
                    and now - dwell_start >= SELECT_HOLD_SECONDS
                ):
                    if idx < len(COLORS):
                        color_idx, erasing = idx, False
                    else:
                        erasing = True
                    armed = False
                if hover is None:
                    armed = True

                # --- pen ---
                pinching, _ = g.is_pinch(hand)
                in_ui = tip_xy[1] <= ui_bottom
                stroke = ERASE_COLOR if erasing else COLORS[color_idx][0]
                width = ERASER_SIZE if erasing else PEN_SIZE

                if pinching and not in_ui:
                    pen_down = True
                    if prev_tip is not None and now - last_clear > 0.5:
                        cv2.line(canvas, prev_tip, tip_xy, stroke, width, cv2.LINE_AA)
                    prev_tip = tip_xy
                elif pinching:
                    prev_tip = None  # finger is up in the palette: no drawing
                elif g.is_open_palm(hand):
                    pen_down = False
                    prev_tip = None
                else:
                    prev_tip = None  # not pinching: hovering, don't draw
            else:
                prev_tip = None
                pen_down = False
                fist_since = None
                hover, dwell_start, armed = None, None, True

            progress = (
                (now - dwell_start) / SELECT_HOLD_SECONDS
                if hover is not None and dwell_start is not None
                else 0.0
            )
            draw_palette(frame, palette, color_idx, erasing, hover, progress)
            draw_hud(frame, pen_down, color_idx, erasing)
            out = cv2.addWeighted(frame, 1.0, canvas, 1.0, 0)
            help_bar(out, "pinch draw | palm lift | fist clear | q quit")
            cv2.imshow(WINDOW, out)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if ord("1") <= key <= ord(str(len(COLORS))):
                color_idx, erasing = key - ord("1"), False
            elif key == ord("e"):
                erasing = True

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
