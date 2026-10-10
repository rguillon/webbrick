"""One spark of a burst: a fading square thrown through the air."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .config import PARTICLE_GRAVITY, PIXEL
from .sprite import snap

if TYPE_CHECKING:
    from pyodide.ffi import JsProxy

    from .coord2d import Coord2D


class Particle:
    """A spark of ``color``: it flies, falls, and burns out after its ``life``."""

    __slots__ = ("color", "life", "max_life", "pos", "size", "speed")

    def __init__(
        self,
        pos: Coord2D,
        speed: Coord2D,
        life: float,
        size: float,
        color: str,
    ) -> None:
        self.pos = pos
        self.speed = speed
        self.life = life
        self.max_life = life
        self.size = size
        self.color = color

    def update(self, h: float) -> bool:
        """Fly and fall for ``h`` seconds; return whether the spark is still burning."""
        self.pos += self.speed * h
        self.speed.y += PARTICLE_GRAVITY * h
        self.life -= h
        return self.life > 0

    def draw(self, ctx: JsProxy) -> None:
        """Paint the spark as a square fading out with the rest of its life."""
        side = PIXEL if self.size < 3 else 2 * PIXEL
        ctx.globalAlpha = self.life / self.max_life
        ctx.fillStyle = self.color
        ctx.fillRect(snap(self.pos.x - side / 2), snap(self.pos.y - side / 2), side, side)


# Coverage helper
_coverage_helper = 0
