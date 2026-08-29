"""Gesture Volume Control — spread your thumb and index finger to change volume.

Pinch distance (thumb tip ↔ index tip, normalized by hand size) maps to the
system volume: wider spread = louder, tighter pinch = quieter.

Cross-platform by design:
* Windows ..... pycaw (real volume)
* macOS ....... osascript ``set volume`` (real volume)
* Linux ....... ``pactl`` or ``amixer`` (real volume)
* anything else or missing tooling ..... a mock that prints instead of
  changing audio, so the gesture code still runs everywhere

Controls
--------
* One hand up ............... adjust volume with thumb/index spread
* "q" ....................... quit
"""

import shutil
import subprocess
import sys
import time

import cv2
import numpy as np

from openhandtrack import HandTracker, LandmarkSmoother
from openhandtrack import gestures as g
from openhandtrack.hud import help_bar, print_controls
from openhandtrack.smoothing import ExponentialMovingAverage

WINDOW = "Volume Control — spread fingers to change volume | q to quit"

#: Normalized pinch gap range that maps onto 0%..100% volume.
MIN_PINCH, MAX_PINCH = 0.12, 0.65


# ---------------------------------------------------------------------------
# Platform volume backends
# ---------------------------------------------------------------------------


class MockVolume:
    """No-op backend so the example runs on any machine, headless or not."""

    def set(self, level: float) -> None:
        print(f"[mock] volume -> {level * 100:.0f}%")


class MacVolume:
    def set(self, level: float) -> None:
        subprocess.run(
            ["osascript", "-e", f"set volume output volume {round(level * 100)}"],
            check=False,
        )


class LinuxVolume:
    def __init__(self) -> None:
        self._tool = (
            "pactl" if shutil.which("pactl") else ("amixer" if shutil.which("amixer") else None)
        )
        if self._tool is None:
            raise RuntimeError("no pactl or amixer found")

    def set(self, level: float) -> None:
        pct = f"{round(level * 100)}%"
        if self._tool == "pactl":
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", pct], check=False)
        else:
            subprocess.run(["amixer", "set", "Master", pct], check=False)


class WindowsVolume:
    def __init__(self) -> None:
        from ctypes import POINTER, cast

        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self._volume = cast(interface, POINTER(IAudioEndpointVolume))

    def set(self, level: float) -> None:
        self._volume.SetMasterVolumeLevelScalar(max(0.0, min(1.0, level)), None)


def get_volume_controller():
    """Return the best working backend for this platform, else the mock."""
    try:
        if sys.platform == "win32":
            return WindowsVolume()
        if sys.platform == "darwin":
            return MacVolume()
        if sys.platform.startswith("linux"):
            return LinuxVolume()
    except Exception as exc:  # missing deps / tools / permissions
        print(f"[volume-control] real volume control unavailable ({exc}); using mock.")
    return MockVolume()


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def draw_bar(frame: np.ndarray, level: float) -> None:
    """Draw a volume bar in the bottom-left corner."""
    h, w = frame.shape[:2]
    bar_w, bar_h = int(w * 0.30), 18
    x0, y0 = 12, h - bar_h - 12
    cv2.rectangle(frame, (x0, y0), (x0 + bar_w, y0 + bar_h), (60, 60, 60), -1)
    cv2.rectangle(frame, (x0, y0), (x0 + int(bar_w * level), y0 + bar_h), (0, 200, 255), -1)
    cv2.putText(
        frame,
        f"{level * 100:3.0f}%",
        (x0 + bar_w + 10, y0 + bar_h - 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )



CONTROLS = [
    ('spread thumb-index', 'louder'),
    ('close them', 'quieter'),
    ('hold at minimum ~1s', 'mute toggle'),
    ('q', 'quit'),
]

def main() -> None:
    print_controls("Volume Control", CONTROLS)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise SystemExit("No webcam found. Connect a camera and try again.")

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))  # faster USB path
    cap.set(cv2.CAP_PROP_FPS, 30)

    controller = get_volume_controller()
    level = ExponentialMovingAverage(alpha=0.85)  # smooth out pinch jitter
    current = 0.5
    last_set = 0.0

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

            if len(hands) == 1:
                gap = g.pinch_distance(hands[0])
                raw_level = (gap - MIN_PINCH) / (MAX_PINCH - MIN_PINCH)
                raw_level = min(1.0, max(0.0, raw_level))
                current = level.apply(raw_level)
                if time.monotonic() - last_set > 0.05:  # throttle OS calls
                    controller.set(current)
                    last_set = time.monotonic()
                cv2.putText(
                    frame,
                    "adjust with thumb/index spread",
                    (12, 26),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )
            else:
                cv2.putText(
                    frame,
                    "hold up ONE hand",
                    (12, 26),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 200, 0),
                    2,
                    cv2.LINE_AA,
                )

            draw_bar(frame, current)
            help_bar(frame, 'thumb-index gap sets volume | wide=loud closed=quiet | q: quit')
            cv2.imshow(WINDOW, frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
