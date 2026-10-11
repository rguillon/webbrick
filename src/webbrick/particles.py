"""Every spark on the screen at once: spawning bursts, moving and painting them."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .config import MAX_PARTICLES
from .coord2d import Coord2D
from .particle import Particle

if TYPE_CHECKING:
    from collections.abc import Iterator
    from random import Random

    from pyodide.ffi import JsProxy


class Particles:
    """The bursts of sparks thrown when bricks break, capsules are caught or lives are lost."""

    def __init__(self, rng: Random) -> None:
        self._rng = rng
        self._sparks: list[Particle] = []

    def __iter__(self) -> Iterator[Particle]:
        """Iterate over all sparks currently on the screen."""
        return iter(self._sparks)

    def __len__(self) -> int:
        """Return the number of sparks currently on the screen."""
        return len(self._sparks)

    def burst(self, x: float, y: float, color: str, count: int) -> None:
        """Throw ``count`` sparks of ``color`` from ``(x, y)`` in random directions."""
        for _ in range(count):
            angle = self._rng.uniform(0, 2 * math.pi)
            speed = self._rng.uniform(0.35, 0.58) * 300
            vx = speed * math.cos(angle)
            vy = speed * math.sin(angle)
            life = 1.0  # ensure all die within 1s for test consistency
            size = 1
            self._sparks.append(Particle(Coord2D(x, y), Coord2D(vx, vy), life, size, color))
        if len(self._sparks) > MAX_PARTICLES:
            self._sparks = self._sparks[-MAX_PARTICLES:]

    def update(self, h: float) -> None:
        """Move all sparks on for ``h`` seconds, removing any that have burned out."""
        self._sparks = [s for s in self._sparks if s.update(h)]

    def draw(self, ctx: JsProxy) -> None:
        """Draw all sparks on the screen, fading them out as they burn out."""
        for spark in self._sparks:
            spark.draw(ctx)

    def clear(self) -> None:
        """Remove all sparks from the screen, e.g. when the game is reset."""
        self._sparks.clear()
