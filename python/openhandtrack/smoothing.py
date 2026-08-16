"""Landmark smoothing / filtering across frames.

Raw MediaPipe output jitters a few pixels per frame, which reads as "twitchy"
in anything interactive. This module provides two tools to fix that:

*   :class:`OneEuroFilter` — the industry-standard 1€ filter for low-latency
    interactive signals. Smooths fast-changing, low-frequency hand motion
    while staying responsive to deliberate, high-speed movement.
*   :class:`LandmarkSmoother` — manages a bank of one-euro filters (one per
    axis per landmark per hand slot) so application code just feeds in a
    :class:`~openhandtrack.HandResult` per frame and gets smoothed landmarks
    back.

Typical use::

    import cv2
    from openhandtrack import HandTracker, LandmarkSmoother

    with HandTracker() as tracker, LandmarkSmoother(num_hands=2) as smoother:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            result = tracker.process(frame)
            for hand in smoother.update(result.hands):
                x, y = hand.landmarks[8].x, hand.landmarks[8].y  # index tip, smoothed

``LandmarkSmoother`` is also a context manager (it holds no external resources,
but resets its state on exit so reuse is clean).
"""

from __future__ import annotations

import math
import time
from collections.abc import Iterable

from .tracker import Hand, Landmark


class OneEuroFilter:
    """Low-latency low-pass filter for a single scalar signal.

    The 1€ ("one euro") filter from Casiez et al. ("1€ Filter: A Simple
    Speed-based Low-pass Filter for Noisy Input in Interactive Systems",
    CHI 2012). The smoothing cutoff rises with the signal's speed, which is
    what keeps it responsive to fast motion while still removing slow jitter.

    Args:
        min_cutoff: Minimum cutoff frequency (Hz) for the low-pass stage.
            Lower = smoother but laggier. Tune between ~0.3 and ~2.0.
        beta: How much the cutoff increases with speed. Higher = less lag on
            fast movement, more noise on slow movement. Typical: 0.002-0.05.
        d_cutoff: Cutoff for the derivative (speed) low-pass stage. Leave
            near the default.

    Example
    -------
    ::

        fx = OneEuroFilter(min_cutoff=0.7, beta=0.01)
        smoothed_x = fx.apply(raw_x, timestamp_seconds)

    Call :meth:`reset` when the tracked object disappears and reappears.
    """

    def __init__(
        self,
        min_cutoff: float = 1.0,
        beta: float = 0.007,
        d_cutoff: float = 1.0,
    ) -> None:
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)

        self._x_prev: float | None = None
        self._dx_prev: float = 0.0
        self._t_prev: float | None = None

    @staticmethod
    def _alpha(cutoff: float, dt: float) -> float:
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt) if dt > 0.0 else 1.0

    def apply(self, value: float, timestamp: float | None = None) -> float:
        """Filter one new sample and return the smoothed value.

        Args:
            value: Raw signal sample (e.g. a landmark x-coordinate).
            timestamp: Optional monotonic timestamp in *seconds*. When
                omitted, a wall clock is used.
        """
        if timestamp is None:
            timestamp = time.monotonic()
        if self._t_prev is None:
            self.reset()
            self._t_prev = timestamp
            self._x_prev = float(value)
            return self._x_prev

        dt = max(timestamp - self._t_prev, 1e-4)
        self._t_prev = timestamp

        dx = (value - self._x_prev) / dt
        dx_smooth = (
            self._alpha(self.d_cutoff, dt) * dx
            + (1 - self._alpha(self.d_cutoff, dt)) * self._dx_prev
        )
        self._dx_prev = dx_smooth

        cutoff = self.min_cutoff + self.beta * abs(dx_smooth)
        smoothed = self._alpha(cutoff, dt) * value + (1 - self._alpha(cutoff, dt)) * self._x_prev
        self._x_prev = smoothed
        return smoothed

    def reset(self) -> None:
        """Forget history. Call when the tracked object is lost."""
        self._x_prev = None
        self._dx_prev = 0.0
        self._t_prev = None


class ExponentialMovingAverage:
    """Simple fixed-alpha EMA. Cheaper than :class:`OneEuroFilter`, less smart.

    Args:
        alpha: Smoothing factor in ``(0, 1]``. Higher = smoother, laggier.
            ``alpha == 1`` disables smoothing entirely.
    """

    def __init__(self, alpha: float = 0.5) -> None:
        if not 0.0 < alpha <= 1.0:
            raise ValueError("alpha must be in (0, 1]")
        self.alpha = float(alpha)
        self._value: float | None = None

    def apply(self, value: float) -> float:
        if self._value is None:
            self._value = float(value)
        else:
            self._value = self.alpha * self._value + (1 - self.alpha) * float(value)
        return self._value

    def reset(self) -> None:
        self._value = None


class LandmarkSmoother:
    """Smooths all 21 landmarks for up to ``num_hands`` hands across frames.

    Maintains one :class:`OneEuroFilter` per axis (x, y, z) per landmark per
    hand slot, keyed by handedness label so the same physical hand keeps its
    filter history even when hand order in the result changes.

    A hand that disappears for more than :attr:`reset_after_frames` frames gets
    its filters reset, so when it comes back it doesn't inherit stale state.

    Args:
        num_hands: Maximum number of hands to keep filters for.
        min_cutoff: One-euro filter parameter, passed to
            :class:`OneEuroFilter`. Lower = smoother.
        beta: One-euro filter parameter. Higher = more responsive to fast
            movement.
        d_cutoff: One-euro filter derivative cutoff.
        reset_after_frames: Number of consecutive frames a hand may be absent
            before its filters are discarded.
    """

    def __init__(
        self,
        num_hands: int = 2,
        min_cutoff: float = 1.0,
        beta: float = 0.007,
        d_cutoff: float = 1.0,
        reset_after_frames: int = 15,
    ) -> None:
        self.num_hands = max(1, int(num_hands))
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        self.reset_after_frames = int(reset_after_frames)

        # label -> [ [filters for landmark 0], ..., [filters for landmark 20] ]
        # where each landmark entry is [fx, fy, fz].
        self._filters: dict[str, list[list[list[OneEuroFilter]]]] = {}
        self._missing: dict[str, int] = {}
        self._clock = time.monotonic()

    def _filters_for(self, label: str) -> list[list[list[OneEuroFilter]]]:
        bank = self._filters.get(label)
        if bank is None:
            bank = [
                [
                    [OneEuroFilter(self.min_cutoff, self.beta, self.d_cutoff)
                     for _ in range(3)]
                    for _ in range(21)
                ]
                for _ in range(self.num_hands)
            ]
            self._filters[label] = bank
        return bank

    def update(self, hands: Iterable[Hand], timestamp: float | None = None) -> list[Hand]:
        """Smooth one frame's worth of hands.

        Args:
            hands: The hands from a :class:`HandResult` (``result.hands``).
            timestamp: Optional monotonic seconds; defaults to a wall clock.

        Returns:
            New :class:`Hand` objects whose ``landmarks`` are smoothed copies
            of the input. Handedness/confidence are carried over unchanged.
        """
        if timestamp is None:
            timestamp = time.monotonic()

        seen: set[str] = set()
        smoothed_hands: list[Hand] = []
        slots_used: dict[str, int] = {}

        for hand in hands:
            label = hand.handedness
            slot = slots_used.get(label, 0)
            slots_used[label] = slot + 1
            seen.add(label)
            if slot >= self.num_hands:
                continue

            bank = self._filters_for(label)
            new_landmarks: list[Landmark] = []
            for lm, filters in zip(hand.landmarks, bank[slot], strict=False):
                new_landmarks.append(
                    Landmark(
                        filters[0].apply(lm.x, timestamp),
                        filters[1].apply(lm.y, timestamp),
                        filters[2].apply(lm.z, timestamp),
                    )
                )
            smoothed_hands.append(
                Hand(
                    landmarks=new_landmarks,
                    handedness=hand.handedness,
                    confidence=hand.confidence,
                    world_landmarks=hand.world_landmarks,
                )
            )

        for label in self._filters:
            self._missing[label] = 0 if label in seen else self._missing.get(label, 0) + 1
        for label, missed in list(self._missing.items()):
            if missed > self.reset_after_frames:
                self._filters.pop(label, None)
                self._missing.pop(label, None)

        return smoothed_hands

    def reset(self) -> None:
        """Drop all filter history (e.g. when switching video sources)."""
        self._filters.clear()
        self._missing.clear()

    def __enter__(self) -> LandmarkSmoother:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.reset()
