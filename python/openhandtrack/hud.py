"""Tiny in-app help overlays shared by the example apps.

Two helpers, zero config:

- :func:`print_controls` — legend printed to the terminal at startup.
- :func:`help_bar` — translucent one-line hint drawn on every video frame.
"""

from __future__ import annotations

import cv2

_FONT = cv2.FONT_HERSHEY_SIMPLEX


def print_controls(app: str, controls: list[tuple[str, str]]) -> None:
    """Print a controls legend to the terminal.

    Args:
        app: App name shown as the block header.
        controls: ``(gesture or key, what it does)`` pairs.
    """
    width = max((len(k) for k, _ in controls), default=0)
    bar = "-" * max(46, width + 30)
    print(f"\n{bar}\n  {app}\n{bar}")
    for key, desc in controls:
        print(f"  {key:<{width}} | {desc}")
    print(f"{bar}\n")


def help_bar(frame, text: str) -> None:
    """Draw a translucent dark hint bar with white text near the frame's bottom-left."""
    height, width = frame.shape[:2]
    scale = max(0.45, min(0.62, width / 1100))
    (tw, th), _ = cv2.getTextSize(text, _FONT, scale, 1)
    pad_x, pad_y = int(12 * scale) + 4, int(7 * scale) + 3
    x0, y0 = 10, height - th - pad_y * 2 - 12
    if x0 < 0 or y0 < 0:
        return
    x1, y1 = min(x0 + tw + pad_x * 2, width - 2), min(y0 + th + pad_y * 2, height - 2)
    roi = frame[y0:y1, x0:x1]
    if roi.size == 0:
        return
    frame[y0:y1, x0:x1] = cv2.multiply(roi, 0.35)
    cv2.putText(
        frame,
        text,
        (x0 + pad_x, y1 - pad_y - 2),
        _FONT,
        scale,
        (240, 240, 240),
        1,
        cv2.LINE_AA,
    )
