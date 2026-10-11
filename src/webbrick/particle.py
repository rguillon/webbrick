"""One spark of a burst: a fading square thrown through the air."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .config import PARTICLE_GRAVITY, PIXEL
from .sprite import snap

_BIG_SIZE = 3  # sparks at least this size are drawn as 2x2 art pixels

if TYPE_CHECKING:
    from pyodide.ffi import JsProxy

    from .coord2d import Coord2D


class Particle:
    """A spark of ``color``: it flies, falls, and burns out after its ``life``."""

    @property
    def x(self) -> float:
        """Return the current x-coordinate."""
        return self.pos.x

    @property
    def vx(self) -> float:
        """Return the current horizontal velocity component."""
        return self.speed.x

    @property
    def vy(self) -> float:
        """Return the current vertical velocity component."""
        return self.speed.y

    @property
    def y(self) -> float:
        """Return the current y-coordinate."""
        return self.pos.y

    def __init__(self, pos: Coord2D, vel: Coord2D, life: float, size: float, color: str) -> None:
        self.pos = pos
        self.speed = vel
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
        side = PIXEL if self.size < _BIG_SIZE else 2 * PIXEL
        ctx.globalAlpha = self.life / self.max_life
        ctx.fillStyle = self.color
        ctx.fillRect(snap(self.pos.x - side / 2), snap(self.pos.y - side / 2), side, side)
        ctx.globalAlpha = 1.0
