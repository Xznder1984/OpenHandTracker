"""Finger Counter — hold up your hand, see how many fingers are extended.

The simplest possible example: one tracker, one gesture helper, one number
on screen. Great first read if you're learning the library.

Controls
--------
* Show your hand .......... the big number counts extended fingers (0-5)
* Press "q" ............... quit
"""

import cv2

from openhandtrack import HandTracker, LandmarkSmoother
from openhandtrack import gestures as g

WINDOW = "Finger Counter — show your hand | q to quit"

#: (tip, pip) landmark pairs used to judge "is this finger straight?"
FINGER_JOINTS = list(g._FINGERS) + [(g.THUMB_TIP, g.THUMB_IP)]


def finger_states(hand) -> list[bool]:
    """Per-finger extended flags: same heuristic as count_extended_fingers."""
    pts = hand.landmarks
    wrist = pts[g.WRIST]

    def far(a, b, ref):
        return (pts[a].x - ref.x) ** 2 + (pts[a].y - ref.y) ** 2 > (pts[b].x - ref.x) ** 2 + (
            pts[b].y - ref.y
        ) ** 2

    four = [far(tip, pip, wrist) for tip, pip in FINGER_JOINTS[:4]]
    # thumb geometry differs: measure against the index MCP, like the library
    thumb = [far(g.THUMB_TIP, g.THUMB_IP, pts[g.INDEX_MCP])]
    return four + thumb


def main() -> None:
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

            # track every other frame, reuse landmarks between: the video
            # still renders at full camera rate, so motion looks smoother
            frame_idx += 1
            if prev_hands is None or frame_idx % 2 == 0:
                prev_hands = smoother.update(tracker.process(frame).hands)
            hands = prev_hands

            if hands:
                hand = hands[0]
                states = finger_states(hand)
                tips = [pair[0] for pair in FINGER_JOINTS]
                for idx, extended in zip(tips, states, strict=True):
                    lm = hand.landmarks[idx]
                    center = (int(lm.x * frame.shape[1]), int(lm.y * frame.shape[0]))
                    color = (0, 220, 0) if extended else (70, 70, 70)
                    cv2.circle(frame, center, 12, color, -1, cv2.LINE_AA)

                label = str(sum(states))
                text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 4.0, 8)[0]
                x = (frame.shape[1] - text_size[0]) // 2
                y = frame.shape[0] - 40
                cv2.putText(
                    frame,
                    label,
                    (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    4.0,
                    (255, 255, 255),
                    8,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    frame,
                    label,
                    (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    4.0,
                    (0, 200, 255),
                    3,
                    cv2.LINE_AA,
                )

            cv2.putText(
                frame,
                "q: quit",
                (12, 26),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (200, 200, 200),
                2,
                cv2.LINE_AA,
            )
            cv2.imshow(WINDOW, frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
