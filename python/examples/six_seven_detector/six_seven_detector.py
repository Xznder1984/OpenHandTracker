"""6-7 Detector — hold up six or seven fingers and witness the brainrot.

A completely serious computer-vision application that monitors your hand at
60fps and alerts you the moment you exhibit SIX or SEVEN extended fingers.
Scientifically proven* to be the funniest possible use of MediaPipe.

*not scientifically proven

Controls
--------
* Show 6 or 7 fingers ....... MEME DETECTED (rainbow alert + counter)
* Anything else ............. stay normal, be humble
* Press "q" ................. quit (sit)
"""

import time

import cv2

from openhandtrack import HandTracker, LandmarkSmoother
from openhandtrack import gestures as g
from openhandtrack.hud import help_bar, print_controls

WINDOW = "6-7 Detector — six sevennn | q to quit"

RAINBOW = [(0, 0, 255), (0, 127, 255), (0, 255, 255), (0, 200, 0), (255, 0, 180), (130, 0, 255)]



CONTROLS = [
    ('6-7 fingers across both hands', 'MEME DETECTED: rainbow + counter'),
    ('anything else', 'be humble'),
    ('q', 'quit (sit)'),
]

def main() -> None:
    print_controls(CONTROLS)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise SystemExit("No webcam found. Connect a camera and try again.")
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FPS, 30)

    with HandTracker(max_hands=2) as tracker, LandmarkSmoother(num_hands=2) as smoother:
        meme_count = 0
        active = False  # inside a 6/7 streak right now?
        prev_hands = None
        frame_idx = 0

        while True:
            ok, frame = cap.read()
            if not ok:
                break

            # track every other frame, reuse landmarks between detections
            frame_idx += 1
            if prev_hands is None or frame_idx % 2 == 0:
                prev_hands = smoother.update(tracker.process(frame).hands)
            hands = prev_hands

            h, w = frame.shape[:2]
            now = time.monotonic()

            if hands:
                count = sum(g.count_extended_fingers(h) for h in hands)
                if count in (6, 7):
                    if not active:
                        meme_count += 1
                        active = True

                        print("\a SIX SEVENNN")  # terminal bell, obviously
                    color = RAINBOW[int(now * 10) % len(RAINBOW)]
                    thickness = 18
                    cv2.rectangle(frame, (0, 0), (w - 1, h - 1), color, thickness)
                    cv2.putText(
                        frame,
                        "SIX",
                        (w // 2 - 150, h // 2 - 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        3,
                        color,
                        14,
                        cv2.LINE_AA,
                    )
                    cv2.putText(
                        frame,
                        "SEVEN",
                        (w // 2 - 190, h // 2 + 70),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        3,
                        color,
                        14,
                        cv2.LINE_AA,
                    )
                else:
                    active = False

                cv2.putText(
                    frame,
                    f"fingers: {count} ({len(hands)} hand{'s' if len(hands) > 1 else ''})",
                    (12, 26),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 220, 255) if count in (6, 7) else (200, 200, 200),
                    2,
                    cv2.LINE_AA,
                )

            cv2.putText(
                frame,
                f"67 count: {meme_count}",
                (12, h - 14),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 180),
                2,
                cv2.LINE_AA,
            )
            help_bar(frame, "show 6 or 7 fingers across BOTH hands... you'll see | q: quit")
            cv2.imshow(WINDOW, frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
