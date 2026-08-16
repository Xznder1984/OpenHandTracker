"""Unit tests for openhandtrack.smoothing (no camera or model needed)."""


import pytest

from openhandtrack import Hand, HandResult, Landmark
from openhandtrack.smoothing import ExponentialMovingAverage, LandmarkSmoother, OneEuroFilter


def make_hand(coords, label="Right"):
    return Hand(
        landmarks=[Landmark(*c) for c in coords],
        handedness=label,
        confidence=0.9,
    )


def jittered_hand(base_x=0.5, noise=0.05, label="Right"):
    """A hand whose index-tip x bounces around base_x with the given noise."""
    coords = [(0.5, 0.9, 0.0), (0.45, 0.80, 0.0), (0.38, 0.74, 0.0), (0.33, 0.70, 0.0),
              (0.28, 0.66, 0.0), (0.45, 0.68, 0.0), (0.45, 0.58, 0.0), (0.45, 0.50, 0.0),
              (0.45, 0.42, 0.0), (0.50, 0.67, 0.0), (0.50, 0.57, 0.0), (0.50, 0.49, 0.0),
              (0.50, 0.41, 0.0), (0.55, 0.68, 0.0), (0.55, 0.58, 0.0), (0.55, 0.50, 0.0),
              (0.55, 0.42, 0.0), (0.60, 0.70, 0.0), (0.60, 0.62, 0.0), (0.60, 0.55, 0.0),
              (0.60, 0.48, 0.0)]
    coords[8] = (base_x, 0.42, 0.0)
    return make_hand(coords, label)


def mean(values):
    return sum(values) / len(values)


def variance(values):
    m = mean(values)
    return sum((v - m) ** 2 for v in values) / len(values)


# ---------------------------------------------------------------------------
# OneEuroFilter
# ---------------------------------------------------------------------------

def test_one_euro_converges_to_constant():
    f = OneEuroFilter(min_cutoff=1.0, beta=0.007)
    out = [f.apply(0.5, timestamp=i * 0.033) for i in range(30)]
    assert abs(out[-1] - 0.5) < 1e-3


def test_one_euro_tracks_step_without_overshoot():
    f = OneEuroFilter(min_cutoff=0.5, beta=0.05)
    out = [f.apply(0.0, timestamp=i * 0.033) for i in range(20)]
    out += [f.apply(1.0, timestamp=(20 + i) * 0.033) for i in range(40)]
    assert out[-1] > 0.95


def test_one_euro_first_sample_passthrough():
    f = OneEuroFilter()
    assert f.apply(0.42) == 0.42


def test_one_euro_reset_forgets_history():
    f = OneEuroFilter()
    f.apply(0.0)
    f.apply(0.0)
    f.reset()
    assert f.apply(1.0) == 1.0


# ---------------------------------------------------------------------------
# ExponentialMovingAverage
# ---------------------------------------------------------------------------

def test_ema_reduces_variance():
    import random

    random.seed(42)
    samples = [0.5 + random.uniform(-0.1, 0.1) for _ in range(300)]
    ema = ExponentialMovingAverage(alpha=0.9)
    out = [ema.apply(s) for s in samples]
    # After warm-up, the EMA output should wobble far less than the input.
    assert variance(out[100:]) < variance(samples[100:]) / 3
    assert abs(mean(out[100:]) - 0.5) < 0.05


def test_ema_invalid_alpha():
    with pytest.raises(ValueError):
        ExponentialMovingAverage(alpha=1.5)


# ---------------------------------------------------------------------------
# LandmarkSmoother
# ---------------------------------------------------------------------------

def test_smoother_reduces_jitter():
    smoother = LandmarkSmoother(num_hands=1, min_cutoff=0.6, beta=0.01)
    raw_xs, smooth_xs = [], []
    for i in range(60):
        x = 0.5 + (0.05 if i % 2 else -0.05)
        raw = jittered_hand(base_x=x)
        raw_xs.append(raw.landmarks[8].x)
        smoothed = smoother.update([raw])[0]
        smooth_xs.append(smoothed.landmarks[8].x)
    assert variance(smooth_xs) < variance(raw_xs) / 5


def test_smoother_keeps_hands_separate_by_label():
    smoother = LandmarkSmoother(num_hands=1)
    left = jittered_hand(label="Left")
    right = jittered_hand(label="Right")
    out = smoother.update([left, right])
    assert [h.handedness for h in out] == ["Left", "Right"]


def test_smoother_resets_after_absent_hand():
    smoother = LandmarkSmoother(num_hands=1, reset_after_frames=3)
    hand = jittered_hand(base_x=0.5)
    smoother.update([hand])
    smoother.update([hand])
    for _ in range(5):
        smoother.update([])  # hand disappears for a while
    assert smoother._filters == {}  # filters were discarded
    out = smoother.update([jittered_hand(base_x=1.0)])
    assert out[0].landmarks[8].x == 1.0  # fresh start, no stale smoothing


def test_smoother_accepts_handresult():
    smoother = LandmarkSmoother(num_hands=1)
    result = HandResult(hands=[jittered_hand()], timestamp_ms=0)
    out = smoother.update(result.hands)
    assert len(out) == 1
