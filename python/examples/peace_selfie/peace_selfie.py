"""Peace Selfie — flash a ✌ and the app counts down and saves a photo.

Demonstrates recognising a *specific* finger combination (index + middle
extended, ring + pinky + thumb folded) and using it as a shutter button.

Controls
--------
* Hold the peace sign ....... 3..2..1 countdown, then saves selfie_N.png
* Anything else ............. cancels the countdown
* Press "q" ................. quit
"""

import time

import cv2

from openhandtrack import HandTracker, LandmarkSmoother
from openhandtrack import gestures as g

WINDOW = "Peace Selfie — hold ✌ to snap a photo | q to quit"
COUNTDOWN_SECONDS = 3.0

#: (tip, pip) landmark pairs used to judge "is this finger straight?"
FINGER_JOINTS = list(g._FINGERS) + [(g.THUMB_TIP, g.THUMB_IP)]


def finger_states(hand) -> list[bool]:
    """Per-finger extended flags (same heuristic as count_extended_fingers)."""
    pts = hand.landmarks
    wrist = pts[g.WRIST]

    def far(a, b, ref):
        return (pts[a].x - ref.x) ** 2 + (pts[a].y - ref.y) ** 2 > (pts[b].x - ref.x) ** 2 + (
            pts[b].y - ref.y
        ) ** 2

    four = [far(tip, pip, wrist) for tip, pip in FINGER_JOINTS[:4]]
    thumb = [far(g.THUMB_TIP, g.THUMB_IP, pts[g.INDEX_MCP])]
    return four + thumb


def is_peace(states: list[bool]) -> bool:
    """Index + middle up, ring + pinky down. Thumb is ignored."""
    return states[0] and states[1] and not states[2] and not states[3]


def main() -> None:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise SystemExit("No webcam found. Connect a camera and try again.")

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))  # faster USB path
    cap.set(cv2.CAP_PROP_FPS, 30)

    with HandTracker(max_hands=1) as tracker, LandmarkSmoother(num_hands=1) as smoother:
        peace_since: float | None = None
        saved = 0
        shot_at = 0.0

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
            now = time.monotonic()

            display = frame.copy()
            if hands:
                states = finger_states(hands[0])
                if is_peace(states):
                    if peace_since is None:
                        peace_since = now
                    remaining = COUNTDOWN_SECONDS - (now - peace_since)
                    if remaining <= 0:
                        name = f"selfie_{saved}.png"
                        cv2.imwrite(name, frame)
                        saved += 1
                        print(f"saved {name}")
                        shot_at = now
                        peace_since = None  # require re-flash for the next shot
                    else:
                        cv2.putText(
                            display,
                            str(int(remaining) + 1),
                            (display.shape[1] // 2 - 30, 120),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            3.5,
                            (0, 220, 255),
                            10,
                            cv2.LINE_AA,
                        )
                else:
                    peace_since = None

                hint = "hold ✌ ..." if is_peace(states) else "show ✌ to arm countdown"
            else:
                peace_since = None
                hint = "no hand in view"

            if now - shot_at < 0.25:  # white flash on save
                display[:] = 255

            cv2.putText(
                display,
                hint,
                (12, 26),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (200, 200, 200),
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                display,
                f"saved: {saved}",
                (12, display.shape[0] - 14),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 200, 255),
                2,
                cv2.LINE_AA,
            )
            cv2.imshow(WINDOW, display)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
