"""One spark of a burst: a fading square thrown through the air."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .config import PARTICLE_GRAVITY, PIXEL
from .sprite import snap

if TYPE_CHECKING:
    from pyodide.ffi import JsProxy


class Particle:
    """A spark of ``color``: it flies, falls, and burns out after its ``life``."""

    __slots__ = ("color", "life", "max_life", "size", "vx", "vy", "x", "y")

    def __init__(  # noqa: PLR0913 - one spark is fully described by these
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        life: float,
        size: float,
        color: str,
    ) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.size = size
        self.color = color

    def update(self, h: float) -> bool:
        """Fly and fall for ``h`` seconds; return whether the spark is still burning."""
        self.x += self.vx * h
        self.y += self.vy * h
        self.vy += PARTICLE_GRAVITY * h
        self.life -= h
        return self.life > 0

    def draw(self, ctx: JsProxy) -> None:
        """Paint the spark as a square fading out with the rest of its life."""
        side = PIXEL if self.size < 3 else 2 * PIXEL  # noqa: PLR2004 - sizes are drawn from 2..4
        ctx.globalAlpha = self.life / self.max_life
        ctx.fillStyle = self.color
        ctx.fillRect(snap(self.x - side / 2), snap(self.y - side / 2), side, side)
