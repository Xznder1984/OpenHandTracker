"""OpenHandTrack — a clean, reusable wrapper around MediaPipe's Hand Landmarker.

Real-time 3D hand tracking for Python, designed to be dropped into your own
projects without fighting MediaPipe's raw task API.

Quick start::

    import cv2
    from openhandtrack import HandTracker

    cap = cv2.VideoCapture(0)
    with HandTracker() as tracker:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            result = tracker.process(frame)
            print(len(result), "hand(s)")
"""

from .gestures import (
    INDEX_DIP,
    INDEX_MCP,
    INDEX_PIP,
    INDEX_TIP,
    MIDDLE_DIP,
    MIDDLE_MCP,
    MIDDLE_PIP,
    MIDDLE_TIP,
    PINKY_DIP,
    PINKY_MCP,
    PINKY_PIP,
    PINKY_TIP,
    RING_DIP,
    RING_MCP,
    RING_PIP,
    RING_TIP,
    THUMB_CMC,
    THUMB_IP,
    THUMB_MCP,
    THUMB_TIP,
    WRIST,
    count_extended_fingers,
    is_fist,
    is_open_palm,
    is_pinch,
    pinch_distance,
    pointing_direction,
)
from .smoothing import (
    ExponentialMovingAverage,
    LandmarkSmoother,
    OneEuroFilter,
)
from .tracker import (
    HANDEDNESS_LABELS,
    MODEL_FILENAME,
    MODEL_URL,
    NUM_LANDMARKS,
    Hand,
    HandResult,
    HandTracker,
    Landmark,
)

__version__ = "0.1.3"

__all__ = [
    # Core tracking
    "HandTracker",
    "HandResult",
    "Hand",
    "Landmark",
    "NUM_LANDMARKS",
    "HANDEDNESS_LABELS",
    "MODEL_URL",
    "MODEL_FILENAME",
    # Smoothing
    "OneEuroFilter",
    "ExponentialMovingAverage",
    "LandmarkSmoother",
    # Gestures
    "count_extended_fingers",
    "is_fist",
    "is_open_palm",
    "is_pinch",
    "pinch_distance",
    "pointing_direction",
    # Landmark index constants
    "WRIST",
    "THUMB_CMC",
    "THUMB_MCP",
    "THUMB_IP",
    "THUMB_TIP",
    "INDEX_MCP",
    "INDEX_PIP",
    "INDEX_DIP",
    "INDEX_TIP",
    "MIDDLE_MCP",
    "MIDDLE_PIP",
    "MIDDLE_DIP",
    "MIDDLE_TIP",
    "RING_MCP",
    "RING_PIP",
    "RING_DIP",
    "RING_TIP",
    "PINKY_MCP",
    "PINKY_PIP",
    "PINKY_DIP",
    "PINKY_TIP",
]
