"""Core hand-tracking wrapper around MediaPipe's Hand Landmarker task.

This module hides MediaPipe's raw task API behind a small, self-contained
interface so that application code never has to think about:

*   The ``mediapipe.tasks`` package layout.
*   Creating and owning the underlying ``HandLandmarker``.
*   Downloading and caching the ``.task`` model file.
*   Converting OpenCV / numpy frames into ``MpImage`` objects.
*   The mirrored-camera handedness quirk (see :class:`HandTracker`).
*   Tracking monotonically increasing timestamps between frames.

The public surface is three dataclasses (:class:`Landmark`, :class:`Hand`,
:class:`HandResult`) and the :class:`HandTracker` class. That's it.

Example
-------
The simplest possible loop, printing the number of hands seen per frame::

    import cv2
    from openhandtrack import HandTracker

    cap = cv2.VideoCapture(0)
    with HandTracker() as tracker:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            result = tracker.process(frame)
            print(f"{len(result)} hand(s) in frame")
"""

from __future__ import annotations

import os
import shutil
import sys
import threading
import time
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:  # pragma: no cover — type hints only, see lazy imports below
    from mediapipe.tasks.python import vision as mp_vision

#: Official float16 Hand Landmarker model, from Google's MediaPipe model zoo.
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)

#: Filename used for the cached model inside the cache directory.
MODEL_FILENAME = "hand_landmarker.task"

#: Number of landmarks MediaPipe produces per hand.
NUM_LANDMARKS = 21

#: Labels MediaPipe reports for handedness.
HANDEDNESS_LABELS = ("Left", "Right")

_SWAP_HANDEDNESS = {"Left": "Right", "Right": "Left"}


@dataclass(frozen=True, slots=True)
class Landmark:
    """A single 3D landmark point in normalized image coordinates.

    ``x`` and ``y`` are normalized to ``[0, 1]`` relative to the frame width
    and height. ``z`` is roughly the *negative* depth in the same normalized
    units (fingertips are closer to the camera than the wrist, so a fingertip
    pointing toward the camera has a more negative ``z``).
    """

    x: float
    y: float
    z: float


@dataclass(slots=True)
class Hand:
    """A detected hand with its 21 landmarks.

    Attributes:
        landmarks: Exactly :data:`NUM_LANDMARKS` points, in MediaPipe's
            canonical order (wrist first, then thumb, index, middle, ring,
            pinky — see ``docs/LANDMARKS.md`` for the full table).
        handedness: ``"Left"`` or ``"Right"``, referring to the *physical*
            hand the person is using (see the ``mirrored`` option on
            :class:`HandTracker` for how this is resolved).
        confidence: Detection/tracking confidence score in ``[0, 1]``.
        world_landmarks: Optional 21 points in 3D *meters* relative to the
            hand's own origin, as produced by MediaPipe. ``None`` when the
            raw result did not include them.
    """

    landmarks: list[Landmark]
    handedness: str
    confidence: float
    world_landmarks: list[Landmark] | None = None

    def __post_init__(self) -> None:
        if self.handedness not in HANDEDNESS_LABELS:
            raise ValueError(
                f"handedness must be one of {HANDEDNESS_LABELS}, got {self.handedness!r}"
            )

    @property
    def palm_center(self) -> Landmark:
        """Average of the wrist and the middle-finger MCP — a stable hand anchor."""
        wrist = self.landmarks[0]
        middle_mcp = self.landmarks[9]
        return Landmark(
            (wrist.x + middle_mcp.x) / 2.0,
            (wrist.y + middle_mcp.y) / 2.0,
            (wrist.z + middle_mcp.z) / 2.0,
        )


@dataclass(slots=True)
class HandResult:
    """Clean result of processing one frame.

    Behaves like a small list of :class:`Hand` objects: you can iterate over
    it, index it, take ``len()``, or check truthiness (``if result:`` is True
    when at least one hand was found). Empty results are returned cleanly —
    never ``None`` — so callers can always assume a valid object.
    """

    hands: list[Hand]
    timestamp_ms: int = 0

    def __bool__(self) -> bool:
        return bool(self.hands)

    def __len__(self) -> int:
        return len(self.hands)

    def __iter__(self) -> Iterator[Hand]:
        return iter(self.hands)

    def __getitem__(self, index: int) -> Hand:
        return self.hands[index]

    @property
    def is_empty(self) -> bool:
        """True when no hand was found in the frame."""
        return not self.hands


class HandTracker:
    """Tracks up to ``max_hands`` hands in a webcam / video frame stream.

    This is the main entry point of the library. Construct one, call
    :meth:`process` with a BGR numpy frame (as produced by ``cv2.VideoCapture``)
    on every video frame, and read the returned :class:`HandResult`.

    Context-manager support means the underlying MediaPipe landmarker is
    always cleaned up, even on exceptions::

        with HandTracker(max_hands=2) as tracker:
            for frame in frames:
                result = tracker.process(frame)

    Args:
        max_hands: Maximum number of hands to detect per frame (1 or 2).
        min_detection_confidence: Minimum confidence for hand detection.
        min_tracking_confidence: Minimum confidence for tracking an already
            detected hand. Lower values track more aggressively but can jitter.
        running_mode: ``"VIDEO"`` (synchronous, one result per :meth:`process`
            call) or ``"LIVE_STREAM"`` (async, MediaPipe runs detection on a
            background thread). Both work exactly the same from the caller's
            perspective — :meth:`process` always returns a :class:`HandResult`.
        mirrored: Whether the input frames are selfie-style *mirrored* images
            (the typical raw webcam feed). See "The mirrored-camera quirk"
            below — this is easy to get wrong.
        model_path: Path to a local ``hand_landmarker.task`` file. When not
            given, the model is downloaded on first use and cached.
        model_url: Override the download URL for the ``.task`` model. Only
            used when ``model_path`` is also unset.

    The mirrored-camera quirk
    -------------------------
    MediaPipe determines handedness *assuming the input image is mirrored* —
    i.e. that it was taken with a front-facing (selfie) camera or otherwise
    flipped horizontally. That assumption holds for most webcam code, which is
    why the default is ``mirrored=True``.

    *   ``mirrored=True`` (default): input is a selfie-style frame. MediaPipe's
        raw output is already correct for the *physical* hand, so it is used
        as-is.
    *   ``mirrored=False``: input is *not* mirrored (rear camera, recorded
        video file, etc.). MediaPipe's labels are flipped, so the tracker
        swaps ``"Left"`` <-> ``"Right"`` before returning.

    When in doubt: hold up your right hand in front of the webcam. If the demo
    reports ``Left``, flip the ``mirrored`` flag.
    """

    def __init__(
        self,
        max_hands: int = 2,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        running_mode: str = "VIDEO",
        mirrored: bool = True,
        model_path: str | Path | None = None,
        model_url: str = MODEL_URL,
    ) -> None:
        if not 1 <= max_hands <= 2:
            raise ValueError("max_hands must be 1 or 2 (MediaPipe supports at most 2)")
        mode = str(running_mode).upper()
        if mode not in ("VIDEO", "LIVE_STREAM"):
            raise ValueError("running_mode must be 'VIDEO' or 'LIVE_STREAM'")

        self.max_hands = max_hands
        self.min_detection_confidence = float(min_detection_confidence)
        self.min_tracking_confidence = float(min_tracking_confidence)
        self.running_mode = mode
        self.mirrored = bool(mirrored)

        self._landmarker: mp_vision.HandLandmarker | None = None
        self._ts_ms = 0
        self._last_clock = time.perf_counter()
        self._lock = threading.Lock()
        self._latest_result = HandResult(hands=[], timestamp_ms=0)

        asset_path = self._resolve_model(model_path, model_url)
        self._landmarker = self._create_landmarker(asset_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, frame: np.ndarray) -> HandResult:
        """Run hand tracking on a single BGR numpy frame.

        Args:
            frame: A ``uint8`` BGR image of shape ``(height, width, 3)``,
                e.g. a frame freshly read from ``cv2.VideoCapture``. Any
                size works — MediaPipe resizes internally.

        Returns:
            A :class:`HandResult`. When no hand is found this is an *empty*
            result (``if not result:`` is True), never an exception and
            never ``None``.

        Raises:
            ValueError: If the frame is not a ``uint8`` 3-channel BGR image.
            RuntimeError: If the landmarker is closed or the frame cannot be
                passed to MediaPipe.
        """
        self._require_open()
        mp_image = self._frame_to_mp_image(frame)
        timestamp_ms = self._next_timestamp_ms()

        if self.running_mode == "VIDEO":
            raw = self._landmarker.detect_for_video(mp_image, timestamp_ms)
            return self._convert_result(raw, timestamp_ms)

        # LIVE_STREAM: detection runs on a MediaPipe background thread and the
        # result arrives via callback. Return the most recent completed result;
        # the newest frame's result lands on the next call. This keeps the
        # caller-facing API identical to VIDEO mode.
        self._landmarker.detect_async(mp_image, timestamp_ms)
        with self._lock:
            return self._latest_result

    def close(self) -> None:
        """Release the underlying MediaPipe landmarker.

        Safe to call multiple times and required (or use a ``with`` block) so
        MediaPipe's native resources are freed promptly.
        """
        landmarker, self._landmarker = self._landmarker, None
        if landmarker is not None:
            landmarker.close()

    def __enter__(self) -> HandTracker:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_open(self) -> None:
        if self._landmarker is None:
            raise RuntimeError("HandTracker has been closed; create a new instance")

    def _next_timestamp_ms(self) -> int:
        """Return a strictly increasing timestamp in milliseconds."""
        now = time.perf_counter()
        dt_ms = int((now - self._last_clock) * 1000)
        self._last_clock = now
        self._ts_ms += max(dt_ms, 1)
        return self._ts_ms

    def _create_landmarker(self, asset_path: Path) -> mp_vision.HandLandmarker:
        # Imported lazily: `import openhandtrack` must stay fast for tests and
        # for users who only need the pure helpers. MediaPipe (and its jax
        # dependency) is heavy and slow to import, so it loads only when a
        # tracker is actually constructed.
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision as mp_vision

        options = mp_vision.HandLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(asset_path)),
            running_mode=(
                mp_vision.RunningMode.VIDEO
                if self.running_mode == "VIDEO"
                else mp_vision.RunningMode.LIVE_STREAM
            ),
            num_hands=self.max_hands,
            min_hand_detection_confidence=self.min_detection_confidence,
            min_hand_presence_confidence=self.min_tracking_confidence,
            min_tracking_confidence=self.min_tracking_confidence,
            result_callback=self._on_live_result if self.running_mode == "LIVE_STREAM" else None,
        )
        return mp_vision.HandLandmarker.create_from_options(options)

    def _on_live_result(self, result, output_image, timestamp_ms: int) -> None:
        converted = self._convert_result(result, timestamp_ms)
        with self._lock:
            self._latest_result = converted

    @staticmethod
    def _frame_to_mp_image(frame: np.ndarray):
        """Wrap an RGB numpy frame in a MediaPipe Image object.

        MediaPipe renamed ``MpImage`` to top-level ``Image`` in 0.10.14+; try
        both so the library works across a range of versions.
        """
        if not isinstance(frame, np.ndarray):
            raise ValueError(f"frame must be a numpy array, got {type(frame).__name__}")
        if frame.ndim != 3 or frame.shape[2] != 3:
            raise ValueError(
                f"frame must be a 3-channel image, got shape {frame.shape}. "
                "Pass a BGR frame from cv2.VideoCapture."
            )
        if frame.dtype != np.uint8:
            raise ValueError(f"frame must be uint8, got dtype {frame.dtype}")

        # OpenCV gives us BGR; MediaPipe expects RGB. The reversed slice view
        # is made contiguous so the MediaPipe Image can consume it directly.
        rgb = np.ascontiguousarray(frame[:, :, ::-1])
        try:
            from mediapipe import Image, ImageFormat  # mediapipe >= 0.10.14
        except ImportError:  # older 0.10.x releases
            from mediapipe.tasks.python.vision import ImageFormat, MpImage as Image  # type: ignore[attr-defined]
        return Image(image_format=ImageFormat.SRGB, data=rgb)

    def _convert_result(self, raw, timestamp_ms: int) -> HandResult:
        hands: list[Hand] = []
        raw_landmarks = getattr(raw, "hand_landmarks", None) or ()
        raw_handedness = getattr(raw, "handedness", None) or ()
        raw_world = getattr(raw, "hand_world_landmarks", None) or ()

        for i, landmark_row in enumerate(raw_landmarks):
            landmarks = [Landmark(p.x, p.y, p.z) for p in landmark_row]

            category = raw_handedness[i][0] if i < len(raw_handedness) else None
            handedness = category.category_name if category else "Right"
            confidence = float(category.score) if category else 0.0

            if not self.mirrored:
                handedness = _SWAP_HANDEDNESS.get(handedness, handedness)

            world = None
            if i < len(raw_world):
                world = [Landmark(p.x, p.y, p.z) for p in raw_world[i]]

            hands.append(Hand(landmarks=landmarks, handedness=handedness,
                              confidence=confidence, world_landmarks=world))

        return HandResult(hands=hands, timestamp_ms=timestamp_ms)

    # ------------------------------------------------------------------
    # Model resolution / download
    # ------------------------------------------------------------------

    @staticmethod
    def _default_cache_dir() -> Path:
        """Package-local `.cache` dir, falling back to the user cache dir."""
        package_cache = Path(__file__).resolve().parent / ".cache"
        try:
            package_cache.mkdir(parents=True, exist_ok=True)
            probe = package_cache / ".write-test"
            probe.touch()
            probe.unlink()
            return package_cache
        except OSError:
            return Path(
                os.environ.get("OPENHANDTRACK_CACHE_DIR")
                or Path.home() / ".cache" / "openhandtrack"
            )

    def _resolve_model(self, model_path: str | Path | None, model_url: str) -> Path:
        env_override = os.environ.get("OPENHANDTRACK_MODEL_PATH")
        if env_override:
            model_path = env_override

        if model_path is not None:
            path = Path(model_path).expanduser()
            if not path.is_file():
                raise FileNotFoundError(
                    f"hand landmarker model not found at {path}. "
                    "Download it from the MediaPipe model zoo or let "
                    "HandTracker download it automatically."
                )
            return path

        cache_dir = self._default_cache_dir()
        cache_dir.mkdir(parents=True, exist_ok=True)
        destination = cache_dir / MODEL_FILENAME
        if destination.is_file():
            return destination
        return self._download_model(model_url, destination)

    def _download_model(self, url: str, destination: Path) -> Path:
        partial = destination.with_suffix(destination.suffix + ".part")
        print(
            f"[openhandtrack] downloading hand-landmarker model -> {destination}",
            file=sys.stderr,
        )
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "openhandtrack/0.1"})
            with (
                urllib.request.urlopen(request, timeout=120) as response,
                open(partial, "wb") as out,
            ):
                shutil.copyfileobj(response, out)
            partial.replace(destination)
        except Exception as exc:
            partial.unlink(missing_ok=True)
            raise RuntimeError(
                f"Failed to download the hand-landmarker model from {url}: {exc}. "
                "You can pass model_path=... to HandTracker to use a local "
                "hand_landmarker.task file instead."
            ) from exc
        return destination
