"""Two-Hand Zoom — pull your hands apart to scroll in, push together to zoom out.

The only example that needs **two** hands at once: it shows how
``max_hands=2`` plus handedness lets you correlate two independent hands.
The distance between them maps onto Ctrl+scroll (pinch-zoom in most apps)
with a dead zone in the middle so small movements don't jitter the zoom.

Controls
--------
* Show both hands ......... baseline distance is captured
* Pull apart / squeeze .... zoom in / out
* Hide one hand ........... resets the baseline
* Press "q" ............... quit
"""

import time

import cv2
from pynput.keyboard import Controller as Keyboard
from pynput.keyboard import Key

from openhandtrack import HandTracker, LandmarkSmoother
from openhandtrack.hud import help_bar, print_controls

WINDOW = "Two-Hand Zoom — spread hands: in, squeeze: out | q to quit"

#: Relative change from baseline that produces one zoom tick.
STEP = 0.06
COOLDOWN = 0.15  # seconds between ticks


def center(hand):
    xs = [lm.x for lm in hand.landmarks]
    ys = [lm.y for lm in hand.landmarks]
    return sum(xs) / len(xs), sum(ys) / len(ys)



CONTROLS = [
    ('show both hands', 'capture baseline'),
    ('spread hands', 'zoom in'),
    ('squeeze hands', 'zoom out'),
    ('hide one hand', 'reset baseline'),
    ('q', 'quit'),
]

def main() -> None:
    print_controls("Two-Hand Zoom", CONTROLS)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise SystemExit("No webcam found. Connect a camera and try again.")

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))  # faster USB path
    cap.set(cv2.CAP_PROP_FPS, 30)

    keyboard = Keyboard()
    baseline: float | None = None
    last_tick = 0.0

    with HandTracker(max_hands=2) as tracker, LandmarkSmoother(num_hands=2) as smoother:
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

            status = "show both hands"
            if len(hands) == 2:
                (ax, ay), (bx, by) = center(hands[0]), center(hands[1])
                dist = ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5

                if baseline is None:
                    baseline = dist
                    status = f"baseline {dist:.2f}"
                else:
                    delta = (dist - baseline) / baseline
                    now = time.monotonic()
                    if abs(delta) >= STEP and now - last_tick >= COOLDOWN:
                        key = Key.right if delta > 0 else Key.left
                        with keyboard.pressed(Key.ctrl):
                            keyboard.press(key)
                            keyboard.release(key)
                        last_tick = now
                        # re-anchor so each tick costs another full STEP
                        baseline = dist - (delta - (STEP if delta > 0 else -STEP)) * baseline
                    status = f"{'IN ◀▶' if delta > 0 else 'OUT ▶◀'} {delta:+.0%}"

                h, w = frame.shape[:2]
                for hand_ in hands:
                    cx, cy = center(hand_)
                    cv2.circle(
                        frame, (int(cx * w), int(cy * h)), 14, (0, 200, 255), -1, cv2.LINE_AA
                    )
            else:
                baseline = None  # require a fresh baseline on re-acquire

            cv2.putText(
                frame,
                status,
                (12, 26),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            help_bar(frame, 'both hands: spread=in squeeze=out | hide one to reset | q: quit')
            cv2.imshow(WINDOW, frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
