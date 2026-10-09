"""Off-screen canvases rendered at the display's real resolution."""

from __future__ import annotations

import math
from typing import Any

from js import document


class Sprite:
    """Off-screen canvas rendered at ``scale`` device px per logical px."""

    __slots__ = ("canvas", "height", "width")

    def __init__(self, canvas: Any, width: float, height: float) -> None:
        self.canvas = canvas
        self.width = width  # logical size, what callers lay out with
        self.height = height

    def draw(self, ctx: Any, x: float, y: float, width: float | None = None, height: float | None = None) -> None:
        """Blit at ``(x, y)`` in logical units (optionally resized)."""
        ctx.drawImage(
            self.canvas,
            x,
            y,
            self.width if width is None else width,
            self.height if height is None else height,
        )


def offscreen(width: float, height: float, scale: float) -> tuple[Sprite, Any]:
    """Create a sprite canvas and a 2D context drawing in logical units."""
    canvas = document.createElement("canvas")
    canvas.width = max(1, math.ceil(width * scale))
    canvas.height = max(1, math.ceil(height * scale))
    g = canvas.getContext("2d")
    g.scale(scale, scale)
    return Sprite(canvas, width, height), g
