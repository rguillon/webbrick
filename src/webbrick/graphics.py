"""Procedural pixel-art graphics: every image in the game is drawn here, no assets.

Sprites are painted in blocks of ``PIXEL`` x ``PIXEL`` logical px ("art
pixels") and blitted with image smoothing off, so they stay blocky at any
display scale. Text uses the 5x7 bitmap font from ``font.py``.
"""

from __future__ import annotations

import random
import re
from typing import TYPE_CHECKING

from .config import (
    BRICK_COLS,
    BRICK_H,
    BRICK_W,
    BULLET_H,
    BULLET_W,
    HEIGHT,
    PADDLE_H,
    PADDLE_W,
    PIXEL,
    POWERUP_H,
    POWERUP_W,
    POWERUPS,
    PREVIEW_CELL_H,
    PREVIEW_CELL_W,
    PREVIEW_GAP,
    ROW_COLORS,
    STEEL,
    WIDTH,
)
from .font import GLYPH_H, GLYPH_W, GLYPHS
from .sprite import Sprite, offscreen

if TYPE_CHECKING:
    from pyodide.ffi import JsProxy

TEXT_SHADOW = "#020617"
_RUN = re.compile("#+")


def mix(color: str, target: str, amount: float) -> str:
    """Blend ``#rrggbb`` ``color`` towards ``target`` by ``amount`` (0..1)."""
    a = [int(color[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(target[i : i + 2], 16) for i in (1, 3, 5)]
    channels = (round(x + (y - x) * amount) for x, y in zip(a, b, strict=True))
    return "#" + "".join(f"{max(0, min(255, c)):02x}" for c in channels)


def block(g: JsProxy, col: int, row: int, w: int = 1, h: int = 1) -> None:
    """Fill ``w`` x ``h`` art pixels at art-pixel position ``(col, row)``."""
    g.fillRect(col * PIXEL, row * PIXEL, w * PIXEL, h * PIXEL)


def pixel_box(g: JsProxy, rect: tuple[float, float, float, float], fill: str, border: str) -> None:
    """Box with a one-art-pixel border and notched corners, in logical px."""
    x, y, w, h = rect
    p = PIXEL
    g.fillStyle = fill
    g.fillRect(x + p, y + p, w - 2 * p, h - 2 * p)
    g.fillStyle = border
    g.fillRect(x + p, y, w - 2 * p, p)
    g.fillRect(x + p, y + h - p, w - 2 * p, p)
    g.fillRect(x, y + p, p, h - 2 * p)
    g.fillRect(x + w - p, y + p, p, h - 2 * p)


def text_width(text: str) -> int:
    """Width of ``text`` in font pixels (one pixel of spacing between glyphs)."""
    return len(text) * (GLYPH_W + 1) - 1


def paint_text(g: JsProxy, text: str, x: float, y: float) -> None:
    """Paint ``text`` (upper-cased) at ``(x, y)`` with the current fill, one px per font pixel."""
    for i, char in enumerate(text.upper()):
        left = x + i * (GLYPH_W + 1)
        for r, row in enumerate(GLYPHS.get(char, GLYPHS["?"])):
            for run in _RUN.finditer(row):
                g.fillRect(left + run.start(), y + r, len(run.group()), 1)


def make_text(text: str, color: str) -> Sprite:
    """Text with a one-pixel drop shadow, meant to be blitted at an integer scale."""
    sprite, g = offscreen(text_width(text) + 1, GLYPH_H + 1)
    g.fillStyle = TEXT_SHADOW
    paint_text(g, text, 1, 1)
    g.fillStyle = color
    paint_text(g, text, 0, 0)
    return sprite


def make_title(text: str) -> Sprite:
    """Title text, each letter tinted along the brick-row rainbow."""
    sprite, g = offscreen(text_width(text) + 1, GLYPH_H + 1)
    g.fillStyle = TEXT_SHADOW
    paint_text(g, text, 1, 1)
    last = len(ROW_COLORS) - 1
    for i, char in enumerate(text):
        pos = last * i / max(1, len(text) - 1)
        low = min(int(pos), last - 1)
        g.fillStyle = mix(ROW_COLORS[low], ROW_COLORS[low + 1], pos - low)
        paint_text(g, char, i * (GLYPH_W + 1), 0)
    return sprite


def _sky_colors(bands: int) -> list[str]:
    """Colours of the background's bands, top to bottom."""
    split = 0.6  # where the middle colour sits
    colors = []
    for k in range(bands):
        t = k / (bands - 1)
        if t < split:
            colors.append(mix("#070b1a", "#10173a", t / split))
        else:
            colors.append(mix("#10173a", "#1a1036", (t - split) / (1 - split)))
    return colors


def make_background() -> Sprite:
    """Night sky in dithered colour bands, a faint grid and a seeded starfield."""
    sprite, g = offscreen(WIDTH, HEIGHT)
    cols, rows = WIDTH // PIXEL, HEIGHT // PIXEL
    bands = 10
    band_h = rows // bands
    colors = _sky_colors(bands)
    for k, color in enumerate(colors):
        g.fillStyle = color
        block(g, 0, k * band_h, cols, band_h)
    for k in range(1, bands):
        # checkerboard of the next band's colour just above each boundary
        g.fillStyle = colors[k]
        for row in (k * band_h - 2, k * band_h - 1):
            for col in range(row % 2, cols, 2):
                block(g, col, row)

    g.globalAlpha = 0.05
    g.fillStyle = "#94a3b8"
    for col in range(0, cols, 12):
        block(g, col, 0, 1, rows)
    for row in range(0, rows, 12):
        block(g, 0, row, cols, 1)

    rng = random.SystemRandom()
    g.fillStyle = "#ffffff"
    for i in range(90):
        col, row = rng.randrange(cols), rng.randrange(rows)
        g.globalAlpha = rng.uniform(0.25, 0.8)
        block(g, col, row)
        if i % 12 == 0:  # a few bright stars get a twinkle cross
            g.globalAlpha = 0.3
            block(g, col - 1, row)
            block(g, col + 1, row)
            block(g, col, row - 1)
            block(g, col, row + 1)
    g.globalAlpha = 1.0
    return sprite


def make_brick_sprite(color: str, hp: int, *, solid: bool, bonus: bool = False) -> Sprite:
    """Bevelled brick; tougher bricks get inset rings, steel gets rivets, bonus bricks a gem."""
    sprite, g = offscreen(BRICK_W, BRICK_H)
    cols, rows = BRICK_W // PIXEL, BRICK_H // PIXEL
    g.fillStyle = color
    block(g, 0, 0, cols, rows)
    g.fillStyle = mix(color, "#ffffff", 0.45)
    block(g, 0, 0, cols - 1, 1)
    block(g, 0, 1, 1, rows - 2)
    g.fillStyle = mix(color, "#000000", 0.45)
    block(g, 1, rows - 1, cols - 1, 1)
    block(g, cols - 1, 0, 1, rows - 1)
    g.fillStyle = "#ffffff"
    block(g, 1, 1)

    if solid:
        for rx, ry in ((2, 2), (cols - 3, 2), (2, rows - 3), (cols - 3, rows - 3)):
            g.fillStyle = "#334155"
            block(g, rx + 1, ry + 1)
            g.fillStyle = "#e2e8f0"
            block(g, rx, ry)
    else:
        g.fillStyle = mix(color, "#ffffff", 0.6)
        for inset in (2, 4)[: hp - 1]:
            w, h = cols - 2 * inset, rows - 2 * inset
            block(g, inset, inset, w, 1)
            block(g, inset, rows - 1 - inset, w, 1)
            block(g, inset, inset, 1, h)
            block(g, cols - 1 - inset, inset, 1, h)

    if bonus:
        center, top = cols // 2, (rows - 5) // 2
        for k, w in enumerate((2, 4, 6, 4, 2)):
            g.fillStyle = "#a16207"
            block(g, center - w // 2, top + k, w, 1)
            g.fillStyle = "#fde047"
            block(g, center - w // 2 + 1, top + k, w - 2, 1)
        g.fillStyle = "#ffffff"
        block(g, center - 1, top + 1)
    return sprite


def _pill(g: JsProxy, area: tuple[int, int], shades: list[str], glow: str, radius: int) -> None:
    """Bar with ``radius`` px of corner cut, one colour per row of ``shades``, and a faint glow."""
    origin, cols = area
    rows = len(shades)
    insets = [max(0, radius - min(r, rows - 1 - r)) for r in range(rows)]
    g.globalAlpha = 0.3
    g.fillStyle = glow
    block(g, origin + insets[0], origin - 1, cols - 2 * insets[0], 1)
    block(g, origin + insets[-1], origin + rows, cols - 2 * insets[-1], 1)
    for r, inset in enumerate(insets):
        block(g, origin + inset - 1, origin + r, cols - 2 * inset + 2, 1)
    g.globalAlpha = 1.0
    for r, (inset, shade) in enumerate(zip(insets, shades, strict=True)):
        g.fillStyle = shade
        block(g, origin + inset, origin + r, cols - 2 * inset, 1)


def make_powerup_sprite(kind: str, pad: int) -> Sprite:
    """Labelled capsule for a falling bonus, ``pad`` px of room for its glow."""
    label, color, _weight = POWERUPS[kind]
    sprite, g = offscreen(POWERUP_W + 2 * pad, POWERUP_H + 2 * pad)
    shades = [mix(color, "#ffffff", 0.6), mix(color, "#ffffff", 0.3), color, color, color]
    shades += [mix(color, "#000000", 0.25), mix(color, "#000000", 0.45), mix(color, "#000000", 0.6)]
    _pill(g, (pad // PIXEL, POWERUP_W // PIXEL), shades[: POWERUP_H // PIXEL], color, 2)
    x = pad + (POWERUP_W - text_width(label)) // 2
    y = pad + (POWERUP_H - GLYPH_H) // 2
    g.fillStyle = TEXT_SHADOW
    paint_text(g, label, x + 1, y + 1)
    g.fillStyle = "#ffffff"
    paint_text(g, label, x, y)
    return sprite


def make_paddle_sprite(pad: int) -> Sprite:
    """Cyan bar with steel end caps, ``pad`` px of room around it for the glow."""
    sprite, g = offscreen(PADDLE_W + 2 * pad, PADDLE_H + 2 * pad)
    origin, cols, rows = pad // PIXEL, PADDLE_W // PIXEL, PADDLE_H // PIXEL
    body = ["#e0f2fe", "#7dd3fc", "#38bdf8", "#38bdf8", "#0ea5e9", "#0369a1", "#075985"]
    caps = ["#f1f5f9", "#cbd5e1", "#94a3b8", "#94a3b8", "#64748b", "#475569", "#334155"]
    _pill(g, (origin, cols), body[:rows], "#38bdf8", 1)
    cap = 5
    for r, shade in enumerate(caps[:rows]):
        inset = 1 if r in (0, rows - 1) else 0
        g.fillStyle = shade
        block(g, origin + inset, origin + r, cap - inset, 1)
        block(g, origin + cols - cap, origin + r, cap - inset, 1)
    g.fillStyle = "#0c4a6e"
    block(g, origin + cap, origin + 1, 1, rows - 2)
    block(g, origin + cols - cap - 1, origin + 1, 1, rows - 2)
    g.fillStyle = "#ffffff"
    block(g, origin + cap + 3, origin + 1, cols - 2 * cap - 6, 1)
    return sprite


def make_cannon_sprite(pad: int) -> Sprite:
    """Two small cannons at the paddle's ends, drawn over it while the gun is active."""
    sprite, g = offscreen(PADDLE_W + 2 * pad, PADDLE_H + 2 * pad)
    origin, cols, rows = pad // PIXEL, PADDLE_W // PIXEL, PADDLE_H // PIXEL
    for left in (origin + 2, origin + cols - 6):
        for dx, shade in enumerate(("#3f6212", "#d9f99d", "#a3e635", "#3f6212")):
            g.fillStyle = shade
            block(g, left + dx, origin - 3, 1, rows + 3)
        g.fillStyle = "#1a2e05"
        block(g, left + 1, origin - 3, 2, 1)
    return sprite


def make_bullet_sprite(pad: int) -> Sprite:
    """Lime bolt with a white tip, ``pad`` px of room around it for the glow."""
    sprite, g = offscreen(BULLET_W + 2 * pad, BULLET_H + 2 * pad)
    origin, cols, rows = pad // PIXEL, BULLET_W // PIXEL, BULLET_H // PIXEL
    g.globalAlpha = 0.35
    g.fillStyle = "#a3e635"
    block(g, origin - 1, origin, cols + 2, rows)
    g.globalAlpha = 1.0
    g.fillStyle = "#84cc16"
    block(g, origin, origin, cols, rows)
    g.fillStyle = "#ffffff"
    block(g, origin, origin, cols, 2)
    return sprite


def make_heart_sprite() -> Sprite:
    """Small heart for the lives counter."""
    pattern = (".##.##.", "#o#####", "#######", ".#####.", "..###..", "...#...")
    sprite, g = offscreen(len(pattern[0]) * PIXEL, len(pattern) * PIXEL)
    for row, line in enumerate(pattern):
        for col, cell in enumerate(line):
            if cell != ".":
                g.fillStyle = "#fecaca" if cell == "o" else "#ef4444"
                block(g, col, row)
    return sprite


def make_preview(rows: tuple[str, ...]) -> Sprite:
    """Miniature of a level layout for its menu card."""
    width = BRICK_COLS * (PREVIEW_CELL_W + PREVIEW_GAP) - PREVIEW_GAP
    height = len(rows) * (PREVIEW_CELL_H + PREVIEW_GAP) - PREVIEW_GAP
    sprite, g = offscreen(width, height)
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            if cell == ".":
                continue
            color = STEEL if cell == "X" else ROW_COLORS[r % len(ROW_COLORS)]
            if cell in "23":
                color = mix(color, "#ffffff", 0.2 * (int(cell) - 1))
            x, y = c * (PREVIEW_CELL_W + PREVIEW_GAP), r * (PREVIEW_CELL_H + PREVIEW_GAP)
            g.fillStyle = color
            g.fillRect(x, y, PREVIEW_CELL_W, PREVIEW_CELL_H)
            g.fillStyle = mix(color, "#ffffff", 0.4)
            g.fillRect(x, y, PREVIEW_CELL_W, PIXEL)
    return sprite
