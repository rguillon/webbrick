"""Every spark on the screen at once: spawning bursts, moving and painting them."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .config import MAX_PARTICLES, PARTICLE_LIFE, PARTICLE_SIZE, PARTICLE_SPEED
from .particle import Particle

if TYPE_CHECKING:
    from collections.abc import Iterator
    from random import Random

    from pyodide.ffi import JsProxy


class Particles:
    """The bursts of sparks thrown when things break, are caught or are lost.

    The game hands over its own ``rng``, so the sparks keep in step with the
    rest of the game's randomness.
    """

    def __init__(self, rng: Random) -> None:
        self._rng = rng
        self._sparks: list[Particle] = []

    def __iter__(self) -> Iterator[Particle]:
        """Iterate over every spark on the screen."""
        return iter(self._sparks)

    def __len__(self) -> int:
        """Return the number of sparks on the screen."""
        return len(self._sparks)

    def burst(self, x: float, y: float, color: str, count: int) -> None:
        """Throw ``count`` sparks of ``color`` out of ``(x, y)``."""
        for _ in range(count):
            angle = self._rng.uniform(0, 2 * math.pi)
            speed = self._rng.uniform(*PARTICLE_SPEED)
            life = self._rng.uniform(*PARTICLE_LIFE)
            size = self._rng.uniform(*PARTICLE_SIZE)
            self._sparks.append(
                Particle(x, y, speed * math.cos(angle), speed * math.sin(angle), life, size, color),
            )
        del self._sparks[:-MAX_PARTICLES]

    def update(self, h: float) -> None:
        """Move every spark on ``h`` seconds and drop the burnt-out ones."""
        self._sparks = [spark for spark in self._sparks if spark.update(h)]

    def draw(self, ctx: JsProxy) -> None:
        """Paint the sparks, then hand the canvas' alpha back."""
        for spark in self:
            spark.draw(ctx)
        ctx.globalAlpha = 1.0

    def clear(self) -> None:
        """Forget every spark."""
        self._sparks.clear()
