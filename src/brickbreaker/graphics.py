"""Procedural graphics: every image in the game is drawn here, no assets."""

from __future__ import annotations

import math
import random
from typing import Any

from .config import (
    BALL_R,
    BRICK_COLS,
    BRICK_H,
    BRICK_W,
    HEIGHT,
    PADDLE_H,
    PADDLE_W,
    PREVIEW_CELL_H,
    PREVIEW_CELL_W,
    PREVIEW_GAP,
    ROW_COLORS,
    STEEL,
    WIDTH,
)
from .sprite import Sprite, offscreen


def mix(color: str, target: str, amount: float) -> str:
    """Blend ``#rrggbb`` ``color`` towards ``target`` by ``amount`` (0..1)."""
    a = [int(color[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(target[i : i + 2], 16) for i in (1, 3, 5)]
    channels = (round(x + (y - x) * amount) for x, y in zip(a, b, strict=True))
    return "#" + "".join(f"{max(0, min(255, c)):02x}" for c in channels)


def round_rect(g: Any, x: float, y: float, w: float, h: float, r: float) -> None:
    """Add a rounded-rectangle path to ``g`` (call ``fill``/``stroke`` after)."""
    g.beginPath()
    g.moveTo(x + r, y)
    g.arcTo(x + w, y, x + w, y + h, r)
    g.arcTo(x + w, y + h, x, y + h, r)
    g.arcTo(x, y + h, x, y, r)
    g.arcTo(x, y, x + w, y, r)
    g.closePath()


def make_background(scale: float) -> Sprite:
    """Night-sky gradient with a faint grid and a seeded starfield."""
    sprite, g = offscreen(WIDTH, HEIGHT, scale)
    grad = g.createLinearGradient(0, 0, 0, HEIGHT)
    grad.addColorStop(0, "#070b1a")
    grad.addColorStop(0.6, "#10173a")
    grad.addColorStop(1, "#1a1036")
    g.fillStyle = grad
    g.fillRect(0, 0, WIDTH, HEIGHT)

    g.strokeStyle = "rgba(148, 163, 184, 0.06)"
    g.lineWidth = 1
    g.beginPath()
    for x in range(0, WIDTH, 24):
        g.moveTo(x + 0.5, 0)
        g.lineTo(x + 0.5, HEIGHT)
    for y in range(0, HEIGHT, 24):
        g.moveTo(0, y + 0.5)
        g.lineTo(WIDTH, y + 0.5)
    g.stroke()

    rng = random.Random(2024)  # noqa: S311 - fixed seed: same starfield every time
    for _ in range(90):
        g.fillStyle = f"rgba(255, 255, 255, {rng.uniform(0.2, 0.8):.2f})"
        g.beginPath()
        g.arc(rng.uniform(0, WIDTH), rng.uniform(0, HEIGHT), rng.uniform(0.4, 1.4), 0, 2 * math.pi)
        g.fill()
    return sprite


def make_brick_sprite(color: str, hp: int, scale: float, *, solid: bool) -> Sprite:
    """Glossy brick; tougher bricks get inset rings, steel gets rivets."""
    sprite, g = offscreen(BRICK_W, BRICK_H, scale)
    grad = g.createLinearGradient(0, 0, 0, BRICK_H)
    grad.addColorStop(0, mix(color, "#ffffff", 0.35))
    grad.addColorStop(0.5, color)
    grad.addColorStop(1, mix(color, "#000000", 0.4))
    g.fillStyle = grad
    round_rect(g, 0, 0, BRICK_W, BRICK_H, 4)
    g.fill()

    g.fillStyle = "rgba(255, 255, 255, 0.28)"
    g.fillRect(4, 2, BRICK_W - 8, 3)

    if solid:
        g.fillStyle = "#cbd5e1"
        for rx, ry in ((5, 5), (BRICK_W - 5, 5), (5, BRICK_H - 5), (BRICK_W - 5, BRICK_H - 5)):
            g.beginPath()
            g.arc(rx, ry, 1.6, 0, 2 * math.pi)
            g.fill()
    else:
        g.strokeStyle = "rgba(255, 255, 255, 0.7)"
        g.lineWidth = 1.5
        for i in range(hp - 1):
            inset = 2.5 + i * 3
            g.strokeRect(inset, inset, BRICK_W - 2 * inset, BRICK_H - 2 * inset)
    return sprite


def make_paddle_sprite(pad: int, scale: float) -> Sprite:
    """Glowing cyan capsule, ``pad`` px of room around it for the glow."""
    sprite, g = offscreen(PADDLE_W + 2 * pad, PADDLE_H + 2 * pad, scale)
    g.shadowColor = "#38bdf8"
    g.shadowBlur = 12 * scale  # shadows ignore the transform
    grad = g.createLinearGradient(0, pad, 0, pad + PADDLE_H)
    grad.addColorStop(0, "#e0f2fe")
    grad.addColorStop(0.5, "#38bdf8")
    grad.addColorStop(1, "#0369a1")
    g.fillStyle = grad
    round_rect(g, pad, pad, PADDLE_W, PADDLE_H, PADDLE_H / 2)
    g.fill()
    g.shadowBlur = 0
    g.fillStyle = "rgba(255, 255, 255, 0.45)"
    round_rect(g, pad + 8, pad + 2, PADDLE_W - 16, 3, 1.5)
    g.fill()
    return sprite


def make_ball_sprite(pad: int, scale: float) -> Sprite:
    """Glowing white-blue ball, ``pad`` px of room around it for the glow."""
    size = 2 * (BALL_R + pad)
    center = size / 2
    sprite, g = offscreen(size, size, scale)
    g.shadowColor = "#bae6fd"
    g.shadowBlur = 14 * scale  # shadows ignore the transform
    grad = g.createRadialGradient(center - 2, center - 2, 1, center, center, BALL_R)
    grad.addColorStop(0, "#ffffff")
    grad.addColorStop(1, "#7dd3fc")
    g.fillStyle = grad
    g.beginPath()
    g.arc(center, center, BALL_R, 0, 2 * math.pi)
    g.fill()
    return sprite


def make_preview(rows: tuple[str, ...], scale: float) -> Sprite:
    """Miniature of a level layout for its menu card."""
    width = BRICK_COLS * (PREVIEW_CELL_W + PREVIEW_GAP) - PREVIEW_GAP
    height = len(rows) * (PREVIEW_CELL_H + PREVIEW_GAP) - PREVIEW_GAP
    sprite, g = offscreen(width, height, scale)
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            if cell == ".":
                continue
            color = STEEL if cell == "X" else ROW_COLORS[r % len(ROW_COLORS)]
            if cell in "23":
                color = mix(color, "#ffffff", 0.2 * (int(cell) - 1))
            g.fillStyle = color
            g.fillRect(
                c * (PREVIEW_CELL_W + PREVIEW_GAP),
                r * (PREVIEW_CELL_H + PREVIEW_GAP),
                PREVIEW_CELL_W,
                PREVIEW_CELL_H,
            )
    return sprite
