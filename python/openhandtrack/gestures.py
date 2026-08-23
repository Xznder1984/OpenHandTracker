"""Derived gesture recognition built on the 21 hand landmarks.

These helpers are the building blocks example projects use. They accept a
:class:`~openhandtrack.Hand` (as returned by ``HandTracker``) *or* any
sequence of 21 landmark objects that expose ``.x`` / ``.y`` / ``.z`` (or
indexable ``(x, y, z)`` tuples) — so they also work on raw MediaPipe data or
hand-rolled landmark lists.

Landmark indices follow MediaPipe's canonical ordering — see
``docs/LANDMARKS.md`` for the anatomical names. The constants defined below
are the ones you'll actually reference in gesture code.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from .tracker import NUM_LANDMARKS, Hand, Landmark

# --- Landmark indices (see docs/LANDMARKS.md) -------------------------------
WRIST = 0
THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20

#: (tip, pip) pairs for the four non-thumb fingers, used by the curl checks.
_FINGERS = (
    (INDEX_TIP, INDEX_PIP),
    (MIDDLE_TIP, MIDDLE_PIP),
    (RING_TIP, RING_PIP),
    (PINKY_TIP, PINKY_PIP),
)

LandmarkLike = Landmark | Sequence[float]
Point = tuple[float, float, float]


def _normalize(hand) -> list[Point]:
    """Coerce a Hand or any 21-landmark sequence into (x, y, z) triples."""
    landmarks = hand.landmarks if isinstance(hand, Hand) else hand
    points: list[Point] = []
    for lm in landmarks:
        if isinstance(lm, Landmark):
            points.append((lm.x, lm.y, lm.z))
        elif isinstance(lm, (tuple, list)):
            points.append((float(lm[0]), float(lm[1]), float(lm[2] if len(lm) > 2 else 0.0)))
        else:  # duck-typed .x/.y/.z
            points.append((float(lm.x), float(lm.y), float(lm.z)))
    if len(points) != NUM_LANDMARKS:
        raise ValueError(
            f"expected {NUM_LANDMARKS} landmarks, got {len(points)}. "
            "Pass a Hand or a sequence of 21 landmark points."
        )
    return points


def _dist(a: Point, b: Point) -> float:
    """3D euclidean distance between two landmark points."""
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def _four_finger_extended(pts: list[Point], mcp: int, pip: int, tip: int) -> bool:
    """A finger is extended when TWO independent distance tests agree.

    Both tests are rigid-motion invariant (pure distances), so they hold at
    any hand orientation — unlike heuristics tied to image axes. Requiring
    agreement suppresses the single-frame landmark jitter that otherwise
    makes live finger counts flicker.
    """
    wrist = pts[WRIST]
    mcp_pt = pts[mcp]
    # curled fingers fold their tip back toward the palm/wrist...
    via_wrist = _dist(pts[tip], wrist) > _dist(pts[pip], wrist)
    # ...while a straight finger keeps its tip well clear of its own knuckle
    via_knuckle = _dist(pts[tip], mcp_pt) > _dist(pts[pip], mcp_pt)
    return via_wrist and via_knuckle


def _thumb_extended(pts: list[Point]) -> bool:
    """Thumb geometry differs from the fingers: judge it against the index
    knuckle (its tuck target when fisted) plus its own CMC base."""
    return _dist(pts[THUMB_TIP], pts[INDEX_MCP]) > _dist(pts[THUMB_IP], pts[INDEX_MCP]) and _dist(
        pts[THUMB_TIP], pts[THUMB_CMC]
    ) > _dist(pts[THUMB_IP], pts[THUMB_CMC])


def finger_states(hand) -> list[bool]:
    """Per-finger extension flags, ordered thumb → index → middle → ring → pinky.

    Uses paired distance tests (see :func:`_four_finger_extended`) that stay
    correct regardless of how the hand is rotated relative to the camera, and
    are far more stable frame-to-frame than single-threshold checks.

    Args:
        hand: A :class:`Hand` or 21-landmark sequence.

    Returns:
        A list of five booleans, one per finger in MediaPipe order.
    """
    pts = _normalize(hand)
    four = [
        _four_finger_extended(pts, mcp, pip, tip)
        for mcp, pip, tip in (
            (INDEX_MCP, INDEX_PIP, INDEX_TIP),
            (MIDDLE_MCP, MIDDLE_PIP, MIDDLE_TIP),
            (RING_MCP, RING_PIP, RING_TIP),
            (PINKY_MCP, PINKY_PIP, PINKY_TIP),
        )
    ]
    return [_thumb_extended(pts)] + four


def count_extended_fingers(hand, include_thumb: bool = True) -> int:
    """Count how many fingers are extended (straight), 0-5.

    Uses rotation-invariant paired distance tests (see :func:`finger_states`),
    so hands held sideways or tilted still count correctly and the result is
    much less twitchy under landmark noise.

    Args:
        hand: A :class:`Hand` or 21-landmark sequence.
        include_thumb: Whether to count the thumb. ``False`` gives a 0-4 range
            and is handy for tests that only care about the four fingers.

    Returns:
        Number of extended fingers (0-5 with the thumb, 0-4 without).
    """
    states = finger_states(hand)
    return sum(states if include_thumb else states[1:])


def is_fist(hand, include_thumb: bool = True) -> bool:
    """True when all four fingers are curled into a fist.

    Args:
        hand: A :class:`Hand` or 21-landmark sequence.
        include_thumb: When False, the thumb is ignored (a "fist" of just the
            four fingers, which is more tolerant of hand geometry).
    """
    states = finger_states(hand)
    if any(states[1:]):
        return False
    if not include_thumb:
        return True
    return not states[0]


def is_open_palm(hand, include_thumb: bool = True) -> bool:
    """True when the hand is fully open (all fingers extended).

    Args:
        hand: A :class:`Hand` or 21-landmark sequence.
        include_thumb: When False, only the four fingers must be extended.
    """
    states = finger_states(hand)
    if not all(states[1:]):
        return False
    if not include_thumb:
        return True
    return states[0]


def pinch_distance(hand) -> float:
    """Normalized distance between the thumb tip and index fingertip.

    The raw pixel gap shrinks when the hand is far from the camera, so the
    distance is normalized by hand size (wrist-to-middle-MCP span). A closed
    pinch is typically below ``0.3``; an open hand is usually above ``0.6``.

    Args:
        hand: A :class:`Hand` or 21-landmark sequence.

    Returns:
        The normalized pinch gap. Lower = closer together.
    """
    pts = _normalize(hand)
    gap = _dist(pts[THUMB_TIP], pts[INDEX_TIP])
    scale = _dist(pts[WRIST], pts[MIDDLE_MCP])
    return gap / scale if scale > 1e-6 else gap


def is_pinch(hand, threshold: float = 0.30) -> tuple[bool, float]:
    """Detect a thumb-index pinch ("grab") gesture.

    Returns a ``(is_pinching, distance)`` tuple — the distance component is
    useful for continuous interactions like pinch-to-scale or pinch-to-volume.

    Args:
        hand: A :class:`Hand` or 21-landmark sequence.
        threshold: Normalized pinch gap below which the hand counts as
            pinching. Tune per scene: ``0.25`` is strict, ``0.4`` is loose.
    """
    distance = pinch_distance(hand)
    return distance < threshold, distance


def pointing_direction(hand) -> tuple[float, float]:
    """Unit vector of the index finger, pointing from its MCP to its tip.

    The returned ``(dx, dy)`` is in normalized image coordinates with ``y``
    pointing *down* (canvas/OpenCV convention), so a finger pointing up at the
    camera yields a negative ``dy``.

    Args:
        hand: A :class:`Hand` or 21-landmark sequence.

    Returns:
        ``(dx, dy)`` unit vector, or ``(0.0, 0.0)`` if the finger has zero
        length in the image plane.
    """
    pts = _normalize(hand)
    dx = pts[INDEX_TIP][0] - pts[INDEX_MCP][0]
    dy = pts[INDEX_TIP][1] - pts[INDEX_MCP][1]
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return (0.0, 0.0)
    return (dx / length, dy / length)
