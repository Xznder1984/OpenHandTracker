# Changelog

All notable changes to the `openhandtrack` Python package.
Dates are release dates on PyPI / GitHub Releases.

## [0.1.4] — 2026-08-23

### Fixed
- Finger counting is now **rotation-invariant and jitter-stable**: a finger
  counts as extended only when two independent distance tests (via wrist and
  via its own knuckle) agree. Hands held sideways or tilted count correctly,
  and live counts no longer flicker with landmark noise.

### Added
- `gestures.finger_states(hand)` — per-finger extension flags
  (`list[bool]`, thumb → pinky).
- Regression tests covering hands rotated 45°–270°.
- The 6-7 Detector example tracks **both hands** and sums finger counts, so
  six or seven fingers is actually reachable (`max_hands=2`).

## [0.1.3] — 2026-08-22

### Fixed
- Import crash (`numpy._core.multiarray failed to import`) caused by shipping
  `opencv-python` alongside MediaPipe's own `opencv-contrib-python`. The
  package no longer declares a direct OpenCV dependency; NumPy is pinned to
  `>=1.26,<2` so pip resolves a consistent set on the first try.

## [0.1.2] — 2026-08-21

### Fixed
- `requires-python = ">=3.11,<3.13"`: MediaPipe ships no wheels for Python
  ≥3.13 (or Intel macOS on its 1.x line), so installs there now fail fast
  with a clear message instead of resolving broken combinations.
- Package `__version__` was stale (`0.1.0`) in released builds; it now stays
  in sync with `pyproject.toml`.

## [0.1.1] — 2026-08-17

### Fixed
- Packaging fixes for the initial PyPI rollout.

> Note: 0.1.1 shipped with the stale version string; prefer ≥ 0.1.2.

## [0.1.0] — 2026-08-16

### Added
- Initial release: `HandTracker` + `LandmarkSmoother` wrappers around the
  MediaPipe Hand Landmarker task API, `gestures` helpers, smoothing filters,
  webcam examples, and a browser demo.
