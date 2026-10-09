"""Off-screen canvases holding pixel-art sprites, one canvas px per logical px."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from js import document

from .config import PIXEL

if TYPE_CHECKING:
    from pyodide.ffi import JsProxy


def snap(value: float) -> int:
    """Round a logical coordinate to the pixel-art grid."""
    return round(value / PIXEL) * PIXEL


class Sprite:
    """Off-screen canvas, blitted with smoothing off so its pixels stay sharp."""

    __slots__ = ("canvas", "height", "width")

    def __init__(self, canvas: JsProxy, width: float, height: float) -> None:
        self.canvas = canvas
        self.width = width  # logical size, what callers lay out with
        self.height = height

    def draw(self, ctx: JsProxy, x: float, y: float, width: float | None = None, height: float | None = None) -> None:
        """Blit at ``(x, y)`` in logical units (optionally resized)."""
        ctx.drawImage(
            self.canvas,
            x,
            y,
            self.width if width is None else width,
            self.height if height is None else height,
        )


def offscreen(width: float, height: float) -> tuple[Sprite, JsProxy]:
    """Create a sprite canvas and a 2D context drawing in logical units.

    The canvas has the sprite's logical size: the main canvas scales it up
    with nearest-neighbour sampling, which is what keeps the art blocky.
    """
    canvas = document.createElement("canvas")
    canvas.width = max(1, math.ceil(width))
    canvas.height = max(1, math.ceil(height))
    return Sprite(canvas, width, height), canvas.getContext("2d")
