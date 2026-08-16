"""Generate OpenHandTrack branding assets (banner + logo) as PNGs.

Renders the 21-point hand-skeleton motif (the same topology MediaPipe uses,
and the same one the web demo draws) with the demo's cyan/orange palette.

Output:
    assets/banner.png  1200x400  hero image for the root README
    assets/logo.png     512x512  square icon (favicon / package icon)

Run:  .venv/bin/python tools/make_assets.py
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"

# --- palette (matches web/src/style.css) ------------------------------------
BG_TOP = (11, 18, 32)
BG_BOTTOM = (15, 26, 48)
CYAN = (34, 211, 238)
ORANGE = (251, 146, 60)
DOT = (226, 232, 240)
INK = (226, 232, 240)
MUTED = (148, 163, 184)

# --- hand topology (x, y in 0..100 space, y down) ---------------------------
POINTS = {
    0: (50, 92),
    1: (38, 80), 2: (28, 74), 3: (22, 68), 4: (17, 61),
    5: (44, 58), 6: (43, 40), 7: (42.5, 30), 8: (42, 20),
    9: (51, 55), 10: (51, 36), 11: (51, 26), 12: (51, 15),
    13: (58, 58), 14: (59, 40), 15: (59.5, 30), 16: (60, 20),
    17: (66, 62), 18: (68, 46), 19: (69, 38), 20: (70, 30),
}
BONES = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def radial_glow(size: tuple[int, int], center, radius, color, max_alpha=70) -> Image:
    """An RGBA image with a soft gaussian glow around `center`."""
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xx - center[0]) ** 2 + (yy - center[1]) ** 2) / radius
    falloff = np.clip(1 - d, 0, 1)
    alpha = (falloff ** 2.2) * max_alpha
    layer = np.zeros((h, w, 4), dtype=np.uint8)
    layer[..., 0], layer[..., 1], layer[..., 2] = color
    layer[..., 3] = alpha.astype(np.uint8)
    return Image.fromarray(layer, "RGBA")


def draw_hand(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], line_w: int, dot_r: int) -> None:
    """Draw the skeleton (gradient bones + dots) into pixel box (x0,y0,x1,y1)."""
    x0, y0, x1, y1 = box
    scale = (x1 - x0) / 100.0
    off_x, off_y = x0, y0

    def px(pt):
        return (off_x + pt[0] * scale, off_y + pt[1] * scale)

    def depth(idx):
        """0.0 near the wrist (cyan) -> 1.0 at the fingertips (orange)."""
        return max(math.dist(POINTS[idx], POINTS[0]) - 8.0, 0.0) / 62.0

    for a, b in BONES:
        pa, pb = px(POINTS[a]), px(POINTS[b])
        t = (depth(a) + depth(b)) / 2
        color = lerp(CYAN, ORANGE, min(t, 1.0))
        draw.line([pa, pb], fill=color, width=line_w, joint="curve")

    for i, pt in POINTS.items():
        x, y = px(pt)
        r = dot_r + (3 if i in (0, 8, 12, 16, 20) else 0)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=DOT, outline=lerp(CYAN, ORANGE, depth(i)), width=2)


def make_banner() -> Image:
    W, H = 1200, 400
    img = Image.new("RGB", (W, H), BG_TOP)
    # vertical gradient background
    for y in range(H):
        img.paste(Image.new("RGB", (1, 1), lerp(BG_TOP, BG_BOTTOM, y / H)), (0, y))
    base = img.convert("RGBA")

    base.alpha_composite(radial_glow((W, H), (210, 200), 320, CYAN, 60))

    draw = ImageDraw.Draw(base)
    draw_hand(draw, (70, 55, 360, 350), line_w=12, dot_r=7)

    # wordmark + tagline
    font_big = _font(58, bold=True)
    font_small = _font(26)
    draw.text((430, 120), "OpenHandTrack", font=font_big, fill=INK)
    draw.text((432, 205), "Real-time 3D hand tracking for Python & the web",
              font=font_small, fill=MUTED)
    draw.text((432, 250), "wraps Google's MediaPipe Hand Landmarker · Apache-2.0",
              font=_font(19), fill=MUTED)

    return base.convert("RGB")


def make_logo() -> Image:
    S = 512
    img = Image.new("RGB", (S, S), BG_TOP)
    for y in range(S):
        img.paste(Image.new("RGB", (1, 1), lerp(BG_TOP, BG_BOTTOM, y / S)), (0, y))
    base = img.convert("RGBA")
    base.alpha_composite(radial_glow((S, S), (S // 2, S // 2), 300, CYAN, 80))

    draw = ImageDraw.Draw(base)
    draw.rounded_rectangle([36, 36, S - 36, S - 36], radius=56, outline=(31, 43, 69), width=4)
    draw_hand(draw, (150, 105, 362, 410), line_w=14, dot_r=8)
    return base.convert("RGB")


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Bold.ttf",
    ]
    if not bold:
        candidates = [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
        ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    make_banner().save(OUT / "banner.png")
    make_logo().save(OUT / "logo.png")
    print("wrote assets/banner.png (1200x400) and assets/logo.png (512x512)")


if __name__ == "__main__":
    main()
