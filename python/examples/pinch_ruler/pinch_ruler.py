"""Pinch Ruler — measure the gap between your thumb and index finger.

A tiny lesson in normalized coordinates: raw pixel distances change with how
far your hand is from the camera, so :func:`gestures.pinch_distance` divides
by hand size (wrist→middle-knuckle span). This example shows that live value
plus a bar meter and the classic "OK / pinch" threshold from ``is_pinch``.

Controls
--------
* Open and close thumb+index ....... watch the measurement move
* Press "q" ........................ quit
"""

import cv2

from openhandtrack import HandTracker, LandmarkSmoother
from openhandtrack import gestures as g
from openhandtrack.hud import help_bar, print_controls

WINDOW = "Pinch Ruler — thumb↔index distance | q to quit"
BAR_W, BAR_H = 400, 36



CONTROLS = [
    ('spread thumb & index', 'meter rises'),
    ('touch them', 'PINCH indicator'),
    ('q', 'quit'),
]

def main() -> None:
    print_controls(CONTROLS)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise SystemExit("No webcam found. Connect a camera and try again.")

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))  # faster USB path
    cap.set(cv2.CAP_PROP_FPS, 30)

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

            if hands:
                hand = hands[0]
                gap = g.pinch_distance(hand)
                pinching, _ = g.is_pinch(hand)

                # draw the measured pair
                h, w = frame.shape[:2]
                for idx in (g.THUMB_TIP, g.INDEX_TIP):
                    lm = hand.landmarks[idx]
                    cv2.circle(
                        frame,
                        (int(lm.x * w), int(lm.y * h)),
                        10,
                        (0, 200, 255) if pinching else (255, 255, 255),
                        -1,
                        cv2.LINE_AA,
                    )
                a = hand.landmarks[g.THUMB_TIP]
                b = hand.landmarks[g.INDEX_TIP]
                cv2.line(
                    frame,
                    (int(a.x * w), int(a.y * h)),
                    (int(b.x * w), int(b.y * h)),
                    (0, 255, 0) if pinching else (90, 90, 90),
                    3,
                )

                # bar meter: pinch_distance is roughly 0.0 (closed)..1.2 (wide)
                filled = int(min(gap / 1.2, 1.0) * BAR_W)
                bx, by = (w - BAR_W) // 2, h - 80
                cv2.rectangle(frame, (bx, by), (bx + BAR_W, by + BAR_H), (40, 40, 40), -1)
                cv2.rectangle(
                    frame,
                    (bx, by),
                    (bx + filled, by + BAR_H),
                    (0, 140, 255) if not pinching else (0, 220, 0),
                    -1,
                )
                cv2.rectangle(frame, (bx, by), (bx + BAR_W, by + BAR_H), (200, 200, 200), 2)

                label = f"{gap:.2f} {'PINCH!' if pinching else ''}"
                cv2.putText(
                    frame,
                    label,
                    (bx, by - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 220, 0) if pinching else (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )

            help_bar(frame, 'thumb<->index gap shown live | touch = PINCH | q: quit')
            cv2.imshow(WINDOW, frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
