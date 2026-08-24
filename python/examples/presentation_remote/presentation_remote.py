"""Presentation Remote — swipe your hand to advance slides.

Swipe your hand (the whole hand, wrist-tip motion) quickly left or right to
send an arrow-key press — works with PowerPoint, Google Slides, Keynote, PDF
viewers, or anything that responds to the arrow keys.

Cross-platform: key presses are sent with ``pynput``. If keyboard control
isn't available (headless box, missing permissions), it prints the would-be
keystroke so the gesture logic still runs.

Controls
--------
* Hand swipes right ..... next slide (Right arrow)
* Hand swipes left ...... previous slide (Left arrow)
* "q" ................... quit

The left/right hand doesn't matter — direction is read from the index
fingertip's screen-space motion.
"""

import collections
import time

import cv2

from openhandtrack import HandTracker, LandmarkSmoother
from openhandtrack import gestures as g
from openhandtrack.hud import help_bar, print_controls

WINDOW = "Presentation Remote — swipe left/right | q to quit"

VELOCITY_THRESHOLD = 1.2  # normalized x-units per second
DEBOUNCE_SECONDS = 0.6  # pause between swipes
SAMPLE_WINDOW = 0.25  # seconds of history used for velocity
FADE_SECONDS = 1.0  # how long the swipe indicator stays on screen


class KeyboardPresser:
    """Sends arrow-key presses, or simulates them when pynput is unavailable."""

    def __init__(self) -> None:
        self._mock = False
        try:
            from pynput.keyboard import Controller, Key

            self._ctrl = Controller()
            self._keys = {"Right": Key.right, "Left": Key.left}
        except Exception as exc:
            print(
                f"[presentation-remote] keyboard control unavailable ({exc}); "
                "simulating keypresses."
            )
            self._mock = True

    def press(self, direction: str) -> None:
        if self._mock:
            print(f"[key] {direction} arrow")
            return
        key = self._keys[direction]
        self._ctrl.press(key)
        self._ctrl.release(key)



CONTROLS = [
    ('fist', 'arm swipe mode'),
    ('swipe left/right (armed)', 'previous/next slide'),
    ('open palm', 'disarm'),
    ('q', 'quit'),
]

def main() -> None:
    print_controls(CONTROLS)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise SystemExit("No webcam found. Connect a camera and try again.")

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))  # faster USB path
    cap.set(cv2.CAP_PROP_FPS, 30)

    keyboard = KeyboardPresser()
    samples: collections.deque[tuple[float, float]] = collections.deque(maxlen=60)
    last_swipe = 0.0
    last_action: tuple[str, float] | None = None  # (direction, when)

    with HandTracker(max_hands=1) as tracker, LandmarkSmoother(num_hands=1) as smoother:
        frame_idx = 0
        prev_hands = None
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            now = time.monotonic()

            # track every other frame, reuse landmarks between: the video
            # still renders at full camera rate, so motion looks smoother
            frame_idx += 1
            if prev_hands is None or frame_idx % 2 == 0:
                prev_hands = smoother.update(tracker.process(frame).hands)
            hands = prev_hands

            if hands:
                tip_x = hands[0].landmarks[g.INDEX_TIP].x
                samples.append((now, tip_x))

                # Velocity over the recent window; direction from dx/dt.
                while samples and samples[0][0] < now - SAMPLE_WINDOW:
                    samples.popleft()
                if len(samples) >= 3 and now - last_swipe > DEBOUNCE_SECONDS:
                    t0, x0 = samples[0]
                    dt = now - t0
                    if dt > 0.05:
                        velocity = (tip_x - x0) / dt
                        if velocity > VELOCITY_THRESHOLD:
                            keyboard.press("Right")
                            last_swipe = now
                            last_action = ("Right", now)
                        elif velocity < -VELOCITY_THRESHOLD:
                            keyboard.press("Left")
                            last_swipe = now
                            last_action = ("Left", now)
            else:
                samples.clear()

            # HUD
            hint = "swipe left/right to navigate slides"
            cv2.putText(
                frame,
                hint,
                (12, 26),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            if last_action and now - last_action[1] < FADE_SECONDS:
                label = "NEXT  >>" if last_action[0] == "Right" else "<<  PREV"
                cv2.putText(
                    frame,
                    label,
                    (12, frame.shape[0] - 14),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 200, 255) if last_action[0] == "Right" else (255, 160, 0),
                    3,
                    cv2.LINE_AA,
                )

            help_bar(frame, 'fist arms mode | swipe L/R = arrow keys | palm disarms | q: quit')
            cv2.imshow(WINDOW, frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
