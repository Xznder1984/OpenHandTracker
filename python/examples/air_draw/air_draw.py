"""Air Draw — pinch to draw in the air, open palm to lift the pen, fist to clear.

Controls
--------
* Pinch (thumb + index together) ..... pen down, draw
* Open palm .......................... pen up (move without drawing)
* Fist held for ~1 second ............ clear the canvas
* Press "q" .......................... quit

This is the smallest complete example of the "library vs. raw API" point:
the entire gesture logic is a handful of calls into
``openhandtrack.gestures`` plus one :class:`HandTracker`.
"""

import time

import cv2
import numpy as np

from openhandtrack import HandTracker, LandmarkSmoother
from openhandtrack import gestures as g

WINDOW = "Air Draw — pinch to draw | open palm to lift | fist 1s to clear | q to quit"
CLEAR_HOLD_SECONDS = 1.0
MAX_HANDS = 1  # the first hand found drives the pen

INSTRUCTIONS = [
    "Pinch: draw",
    "Palm: lift pen",
    "Fist 1s: clear",
]


def draw_hud(frame: np.ndarray, pen_down: bool) -> None:
    """Overlay the control legend and pen state on the video frame."""
    for i, line in enumerate(INSTRUCTIONS):
        cv2.putText(frame, line, (12, 26 + i * 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (255, 255, 255), 2, cv2.LINE_AA)
    state = "PEN DOWN — drawing" if pen_down else "PEN UP — not drawing"
    color = (0, 200, 255) if pen_down else (160, 160, 160)
    cv2.putText(frame, state, (12, frame.shape[0] - 14), cv2.FONT_HERSHEY_SIMPLEX,
                0.65, color, 2, cv2.LINE_AA)


def main() -> None:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise SystemExit("No webcam found. Connect a camera and try again.")

    with HandTracker(max_hands=MAX_HANDS) as tracker, LandmarkSmoother(
        num_hands=MAX_HANDS
    ) as smoother:
        canvas: np.ndarray | None = None
        prev_tip: tuple[int, int] | None = None
        pen_down = False
        fist_since: float | None = None
        last_clear = 0.0

        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)  # selfie view; matches mirrored=True default
            if canvas is None or canvas.shape[:2] != frame.shape[:2]:
                canvas = np.zeros_like(frame)

            result = tracker.process(frame)
            hands = smoother.update(result.hands)
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

                pinching, _ = g.is_pinch(hand)
                if pinching:
                    pen_down = True
                    if prev_tip is not None and now - last_clear > 0.5:
                        cv2.line(canvas, prev_tip, tip_xy, (0, 200, 255), 5, cv2.LINE_AA)
                    prev_tip = tip_xy
                elif g.is_open_palm(hand):
                    pen_down = False
                    prev_tip = None
                else:
                    prev_tip = None  # not pinching: hovering, don't draw
            else:
                prev_tip = None
                pen_down = False
                fist_since = None

            draw_hud(frame, pen_down)
            cv2.imshow(WINDOW, cv2.addWeighted(frame, 1.0, canvas, 1.0, 0))

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
