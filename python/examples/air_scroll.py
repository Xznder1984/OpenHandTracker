"""Air Scroll — point up or down to scroll any window, hands-free.

The index finger becomes a joystick: point above the middle of the frame to
scroll up, below it to scroll down. The further from the middle, the faster.
A fist locks scrolling (great for reading); an open palm stops it.

Controls
--------
* Point up / down ....... scroll (speed scales with distance from centre)
* Fist .................. lock in place
* Open palm ............. stop scrolling
* Press "q" ............. quit
"""

import time

import cv2
from pynput.keyboard import Controller as Keyboard
from pynput.keyboard import Key

from openhandtrack import HandTracker, LandmarkSmoother
from openhandtrack import gestures as g
from openhandtrack.hud import help_bar, print_controls

WINDOW = "Air Scroll — point up/down to scroll | fist: lock | palm: stop | q to quit"

#: Normalized y-distance from centre at which max scroll speed is reached.
FAST_AT = 0.30
MAX_STEPS_PER_TICK = 3
TICK = 0.05  # seconds between scroll bursts



CONTROLS = [
    ('point above midline', 'scroll up'),
    ('point below midline', 'scroll down'),
    ('farther from centre', 'faster'),
    ('fist', 'lock position'),
    ('open palm', 'stop'),
    ('q', 'quit'),
]

def main() -> None:
    print_controls("Air Scroll", CONTROLS)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise SystemExit("No webcam found. Connect a camera and try again.")

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))  # faster USB path
    cap.set(cv2.CAP_PROP_FPS, 30)

    keyboard = Keyboard()
    locked = False
    last_tick = 0.0

    with HandTracker(max_hands=1) as tracker, LandmarkSmoother(num_hands=1) as smoother:
        frame_idx = 0
        prev_hands = None
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)

            # track every other frame, reuse landmarks between: the video
            # still renders at full camera rate, so motion looks smoother
            frame_idx += 1
            if prev_hands is None or frame_idx % 2 == 0:
                prev_hands = smoother.update(tracker.process(frame).hands)
            hands = prev_hands

            state, speed = "no hand", 0.0
            if hands:
                hand = hands[0]
                tip_y = hand.landmarks[g.INDEX_TIP].y

                if g.is_fist(hand):
                    locked = True
                elif g.is_open_palm(hand):
                    locked = False

                if locked:
                    state, speed = "locked", 0.0
                elif tip_y < 0.5 - FAST_AT:
                    state, speed = "scrolling ▲", -1.0
                elif tip_y > 0.5 + FAST_AT:
                    state, speed = "scrolling ▼", 1.0
                else:
                    zone = abs(tip_y - 0.5) / FAST_AT  # 0..1 inside the band
                    direction = -1.0 if tip_y < 0.5 else 1.0
                    speed = direction * max(zone * 2 - 1.0, 0.0)
                    state = f"scrolling {'▲' if speed < 0 else '▼'}" if speed else "neutral"

                now = time.monotonic()
                steps = int(speed * MAX_STEPS_PER_TICK)
                if steps and now - last_tick >= TICK:
                    key = Key.page_up if steps < 0 else Key.page_down
                    for _ in range(abs(steps)):
                        keyboard.press(key)
                        keyboard.release(key)
                    last_tick = now

            bar_x = frame.shape[1] // 2
            cv2.line(
                frame,
                (bar_x, int(frame.shape[0] * 0.25)),
                (bar_x, int(frame.shape[0] * 0.75)),
                (90, 90, 90),
                2,
            )
            cv2.putText(
                frame, state, (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2, cv2.LINE_AA
            )
            help_bar(frame, 'point up/down: scroll | fist: lock | palm: stop | q: quit')
            cv2.imshow(WINDOW, frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
