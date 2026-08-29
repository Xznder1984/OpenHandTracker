"""Virtual Mouse — steer the cursor with your index finger, pinch to click.

The index fingertip drives the OS cursor across the whole screen while an
open palm pauses control (so you can reposition without teleporting the
pointer). Pinch = press-and-hold; release = click.

Controls
--------
* Move index finger ...... cursor follows
* Open palm .............. pause cursor control
* Pinch + move ........... left button held (drag)
* Release pinch .......... click / release
* Press "q" .............. quit

Requires accessibility permission to control the mouse (macOS will prompt).
"""

import ctypes
import os
import subprocess

import cv2
from pynput.mouse import Button
from pynput.mouse import Controller as MouseController

from openhandtrack import HandTracker, LandmarkSmoother
from openhandtrack import gestures as g
from openhandtrack.hud import help_bar, print_controls
from openhandtrack.smoothing import ExponentialMovingAverage

WINDOW = "Virtual Mouse — finger moves cursor | palm: pause | pinch: click | q to quit"


def screen_size() -> tuple[int, int]:
    """Best-effort screen resolution; falls back to a sane 1920x1080."""
    try:
        if os.name == "nt":
            user32 = ctypes.windll.user32
            return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        out = subprocess.run(
            ["osascript", "-e", 'tell application "Finder" to get bounds of window of desktop'],
            capture_output=True,
            text=True,
            check=False,
        ).stdout
        if out:
            _, _, w, h = map(int, out.split(","))
            return w, h
    except Exception:
        pass
    return 1920, 1080



CONTROLS = [
    ('move index finger', 'cursor follows'),
    ('pinch & hold', 'left button down (drag)'),
    ('release pinch', 'click'),
    ('open palm', 'pause control'),
    ('q', 'quit'),
]

def main() -> None:
    print_controls("Virtual Mouse", CONTROLS)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise SystemExit("No webcam found. Connect a camera and try again.")

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))  # faster USB path
    cap.set(cv2.CAP_PROP_FPS, 30)

    mouse = MouseController()
    screen_w, screen_h = screen_size()

    smooth_x = ExponentialMovingAverage(alpha=0.35)
    smooth_y = ExponentialMovingAverage(alpha=0.35)
    pressing = False

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

            status = "no hand"
            if hands:
                hand = hands[0]
                pinching, _ = g.is_pinch(hand)
                paused = g.is_open_palm(hand)

                if not paused:
                    tip = hand.landmarks[g.INDEX_TIP]
                    sx = smooth_x.apply(tip.x)
                    sy = smooth_y.apply(tip.y)
                    px = int(min(max(sx, 0.0), 1.0) * screen_w)
                    py = int(min(max(sy, 0.0), 1.0) * screen_h)
                    mouse.position = (px, py)

                    if pinching and not pressing:
                        mouse.press(Button.left)
                        pressing = True
                    elif not pinching and pressing:
                        mouse.release(Button.left)
                        pressing = False
                elif pressing:
                    mouse.release(Button.left)
                    pressing = False

                status = "paused" if paused else ("dragging" if pressing else "controlling")

            color = (60, 60, 60) if status in ("paused", "no hand") else (0, 200, 255)
            cv2.putText(
                frame,
                status.upper(),
                (12, 26),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2,
                cv2.LINE_AA,
            )
            help_bar(frame, 'index moves cursor | pinch: click/drag | palm: pause | q: quit')
            cv2.imshow(WINDOW, frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                if pressing:
                    mouse.release(Button.left)
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
