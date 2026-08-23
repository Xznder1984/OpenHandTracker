"""Unit tests for openhandtrack.gestures using synthetic landmark coordinates."""

import math

import pytest

from openhandtrack import Hand, Landmark
from openhandtrack import gestures as g

# ---------------------------------------------------------------------------
# Synthetic landmark sets: 21 (x, y, z) points each.
# ---------------------------------------------------------------------------

OPEN_PALM = [
    (0.50, 0.90, 0.00),  # 0  wrist
    (0.45, 0.80, -0.01),  # 1  thumb cmc
    (0.38, 0.74, -0.02),  # 2  thumb mcp
    (0.33, 0.70, -0.02),  # 3  thumb ip
    (0.28, 0.66, -0.03),  # 4  thumb tip
    (0.45, 0.68, -0.01),  # 5  index mcp
    (0.45, 0.58, -0.02),  # 6  index pip
    (0.45, 0.50, -0.02),  # 7  index dip
    (0.45, 0.42, -0.03),  # 8  index tip
    (0.50, 0.67, -0.01),  # 9  middle mcp
    (0.50, 0.57, -0.02),  # 10 middle pip
    (0.50, 0.49, -0.02),  # 11 middle dip
    (0.50, 0.41, -0.03),  # 12 middle tip
    (0.55, 0.68, -0.01),  # 13 ring mcp
    (0.55, 0.58, -0.02),  # 14 ring pip
    (0.55, 0.50, -0.02),  # 15 ring dip
    (0.55, 0.42, -0.03),  # 16 ring tip
    (0.60, 0.70, -0.01),  # 17 pinky mcp
    (0.60, 0.62, -0.02),  # 18 pinky pip
    (0.60, 0.55, -0.02),  # 19 pinky dip
    (0.60, 0.48, -0.03),  # 20 pinky tip
]

FIST = [
    (0.50, 0.90, 0.00),  # 0  wrist
    (0.46, 0.82, -0.02),  # 1  thumb cmc
    (0.42, 0.80, -0.03),  # 2  thumb mcp
    (0.47, 0.84, -0.04),  # 3  thumb ip  (curled in)
    (0.48, 0.82, -0.05),  # 4  thumb tip (tucked against the palm)
    (0.46, 0.78, -0.02),  # 5  index mcp
    (0.45, 0.80, -0.03),  # 6  index pip
    (0.46, 0.83, -0.04),  # 7  index dip
    (0.48, 0.85, -0.05),  # 8  index tip (curled toward palm)
    (0.50, 0.77, -0.02),  # 9  middle mcp
    (0.49, 0.79, -0.03),  # 10 middle pip
    (0.50, 0.82, -0.04),  # 11 middle dip
    (0.51, 0.84, -0.05),  # 12 middle tip
    (0.54, 0.78, -0.02),  # 13 ring mcp
    (0.55, 0.80, -0.03),  # 14 ring pip
    (0.54, 0.83, -0.04),  # 15 ring dip
    (0.53, 0.85, -0.05),  # 16 ring tip
    (0.58, 0.80, -0.02),  # 17 pinky mcp
    (0.59, 0.82, -0.03),  # 18 pinky pip
    (0.58, 0.85, -0.04),  # 19 pinky dip
    (0.57, 0.87, -0.05),  # 20 pinky tip
]


def make_hand(coords):
    return Hand(
        landmarks=[Landmark(*c) for c in coords],
        handedness="Right",
        confidence=0.9,
    )


@pytest.fixture
def open_hand():
    return make_hand(OPEN_PALM)


@pytest.fixture
def fist_hand():
    return make_hand(FIST)


def test_count_extended_fingers_open_palm(open_hand):
    assert g.count_extended_fingers(open_hand) == 5
    assert g.count_extended_fingers(open_hand, include_thumb=False) == 4


def test_count_extended_fingers_fist(fist_hand):
    assert g.count_extended_fingers(fist_hand) == 0


def test_is_open_palm(open_hand, fist_hand):
    assert g.is_open_palm(open_hand) is True
    assert g.is_open_palm(fist_hand) is False
    assert g.is_open_palm(fist_hand, include_thumb=False) is False


def test_is_fist(open_hand, fist_hand):
    assert g.is_fist(fist_hand) is True
    assert g.is_fist(open_hand) is False


def _rotate(coords, degrees):
    """Rotate landmarks around their centroid in the image plane."""
    rad = math.radians(degrees)
    cos, sin = math.cos(rad), math.sin(rad)
    cx = sum(p[0] for p in coords) / len(coords)
    cy = sum(p[1] for p in coords) / len(coords)
    return [
        (cx + dx * cos - dy * sin, cy + dx * sin + dy * cos, z)
        for x, y, z in ((p[0], p[1], p[2]) for p in coords)
        for dx, dy in [(x - cx, y - cy)]
    ]


@pytest.mark.parametrize("angle", [45, 90, 135, 180, 225, 270])
def test_finger_count_is_rotation_invariant(open_hand, fist_hand, angle):
    """Tilting the hand must not change the count (the old wrist-distance
    heuristic misread hands held sideways — this pins the fix)."""
    assert g.count_extended_fingers(make_hand(_rotate(OPEN_PALM, angle))) == 5
    assert g.count_extended_fingers(make_hand(_rotate(FIST, angle))) == 0
    assert g.is_open_palm(make_hand(_rotate(OPEN_PALM, angle))) is True
    assert g.is_fist(make_hand(_rotate(FIST, angle))) is True


def test_finger_states_matches_count_and_order(open_hand, fist_hand):
    states_open = g.finger_states(open_hand)
    states_fist = g.finger_states(fist_hand)
    assert states_open == [True, True, True, True, True]
    assert states_fist == [False, False, False, False, False]
    assert sum(states_open) == g.count_extended_fingers(open_hand)
    # partial pose: index + middle up only (a "peace" hand)
    coords = [list(c) for c in FIST]
    coords[g.INDEX_TIP] = (0.45, 0.60, -0.03)
    coords[g.MIDDLE_TIP] = (0.50, 0.59, -0.03)
    partial = make_hand(coords)
    assert g.finger_states(partial) == [False, True, True, False, False]
    assert g.count_extended_fingers(partial) == 2


def test_is_pinch(open_hand):
    pinching, distance = g.is_pinch(open_hand)
    assert pinching is False
    assert 0.0 < distance < 2.0

    coords = [list(c) for c in OPEN_PALM]
    coords[g.THUMB_TIP] = (0.455, 0.45, -0.04)  # pinch: thumb tip on index tip
    pinching, distance = g.is_pinch(make_hand(coords))
    assert pinching is True
    assert distance < 0.30


def test_pinch_distance_normalizes_by_hand_size(open_hand):
    big = make_hand([(x * 2.0, y * 2.0, z) for x, y, z in OPEN_PALM])
    assert math.isclose(g.pinch_distance(big), g.pinch_distance(open_hand), rel_tol=0.01)


def test_pointing_direction(open_hand):
    dx, dy = g.pointing_direction(open_hand)
    assert math.isclose(dx, 0.0, abs_tol=1e-6)
    assert math.isclose(dy, -1.0, abs_tol=1e-6)
    assert math.isclose(math.hypot(dx, dy), 1.0)


def test_landmark_constants_match_mediapipe_order():
    assert g.THUMB_TIP == 4
    assert g.INDEX_MCP == 5
    assert g.INDEX_TIP == 8
    assert g.MIDDLE_TIP == 12
    assert g.RING_TIP == 16
    assert g.PINKY_TIP == 20


def test_accepts_raw_tuples():
    """gestures should also work on plain (x, y, z) sequences, no Hand object."""
    assert g.count_extended_fingers(OPEN_PALM) == 5
    assert g.is_fist(FIST) is True
    dx, dy = g.pointing_direction(OPEN_PALM)
    assert math.isclose(dy, -1.0, abs_tol=1e-6)


def test_rejects_wrong_landmark_count():
    with pytest.raises(ValueError):
        g.count_extended_fingers([(0.0, 0.0, 0.0)] * 5)
