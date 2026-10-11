# Copyright (c) 2024-2025 Renaud de Landtsheer
# SPDX-License-Identifier: MIT

"""The bouncing coloured sphere that the player controls in the game."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .config import BALL_R, HEIGHT, PIXEL, TRAIL_LEN
from .coord2d import Coord2D

if TYPE_CHECKING:
    from pyodide.ffi import JsProxy

    from .sprite import Sprite


def mix(color: str, target: str, amount: float) -> str:
    """Blend ``#rrggbb`` ``color`` towards ``target`` by ``amount`` (0..1)."""
    a = [int(color[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(target[i : i + 2], 16) for i in (1, 3, 5)]
    channels = (round(x + (y - x) * amount) for x, y in zip(a, b, strict=True))
    return "#" + "".join(f"{max(0, min(255, c)):02x}" for c in channels)


def block(g: JsProxy, col: int, row: int, w: int = 1, h: int = 1) -> None:
    """Fill ``w`` x ``h`` art pixels at art-pixel position ``(col, row)``."""
    g.fillRect(col * PIXEL, row * PIXEL, w * PIXEL, h * PIXEL)


class Ball:
    """One ball: position, velocity (px/s), its motion trail, and whether it burns."""

    COLOR = "#7dd3fc"  # trail colour while cool
    FIRE_COLOR = "#f97316"  # trail colour while on fire
    CORE_COLOR = "#ffffff"
    EDGE_COLOR = "#7dd3fc"
    GLOW_COLOR = "#bae6fd"
    FIRE_CORE = "#fef08a"
    FIRE_EDGE = "#f97316"
    FIRE_GLOW = "#fb923c"

    @property
    def x(self) -> float:
        """Return the current x-coordinate."""
        return self.pos.x

    @x.setter
    def x(self, value: float) -> None:
        self.pos.x = value

    @property
    def y(self) -> float:
        """Return the current y-coordinate."""
        return self.pos.y

    @y.setter
    def y(self, value: float) -> None:
        self.pos.y = value

    @property
    def dx(self) -> float:
        """Return the current horizontal velocity component."""
        return self.vel.x

    @dx.setter
    def dx(self, value: float) -> None:
        self.vel.x = value

    @property
    def dy(self) -> float:
        """Return the current vertical velocity component."""
        return self.vel.y

    @dy.setter
    def dy(self, value: float) -> None:
        self.vel.y = value

    @property
    def radius(self) -> float:
        """Return the ball's radius in pixels."""
        return getattr(self, "_radius", BALL_R)

    @radius.setter
    def radius(self, value: float) -> None:
        self._radius = value

    def __init__(  # noqa: PLR0913
        self,
        x: float,
        y: float,
        dx: float = 0.0,
        dy: float = 0.0,
        *,
        fire: bool = False,
        radius: float | None = None,
    ) -> None:
        """Expose legacy flat attributes for compatibility with tests."""
        self.pos = Coord2D(x, y)
        self.vel = Coord2D(dx, dy)
        self.fire = fire
        self.trail: list[tuple[float, float]] = []
        if radius is not None:
            self._radius = radius

    def update(self, h: float) -> None:
        """Move on for ``h`` seconds, remembering where the ball has been."""
        self.pos += self.vel * h
        self.trail.append((self.pos.x, self.pos.y))
        if len(self.trail) > TRAIL_LEN:
            self.trail.pop(0)

    @property
    def speed(self) -> float:
        """Distance travelled per second."""
        return math.hypot(self.vel.x, self.vel.y)

    @speed.setter
    def speed(self, value: float) -> None:
        """Head at ``value`` px/s along the current heading; a parked ball stays parked."""
        current = self.speed
        if current > 0.0:
            self.vel.x *= value / current
            self.vel.y *= value / current

    @property
    def color(self) -> str:
        """The trail colour: the pierce bonus paints the ball fiery."""
        return self.FIRE_COLOR if self.fire else self.COLOR

    @property
    def fallen(self) -> bool:
        """Whether the ball has dropped out below the floor."""
        return self.pos.y - self.radius > HEIGHT

    def bounce_x(self, x: float) -> None:
        """Bounce off a vertical face, coming to rest at ``x`` (a side wall or a brick)."""
        self.pos.x = x
        self.vel.x = -self.vel.x

    def bounce_y(self, y: float) -> None:
        """Bounce off a horizontal face, coming to rest at ``y`` (the ceiling or a brick)."""
        self.pos.y = y
        self.vel.y = -self.vel.y

    def bounce_paddle(self, y: float, angle: float, speed: float) -> None:
        """Leave the paddle's face at ``y``, heading ``angle`` from vertical at ``speed`` px/s."""
        self.pos.y = y
        self.head_at(angle, speed)

    def head_at(self, angle: float, speed: float) -> None:
        """Face ``angle`` from straight up, travelling at ``speed`` px/s."""
        self.vel.x = speed * math.sin(angle)
        self.vel.y = -speed * math.cos(angle)

    @staticmethod
    def make_sprite(
        pad: int,
        radius: float = BALL_R,
        *,
        fire: bool = False,
    ) -> Sprite:
        """Create a pixel ball sprite for the given radius and fire state.

        Args:
            pad: padding around the ball for glow effects
            radius: ball radius in pixels (default BALL_R)
            fire: whether to use fiery colors (default False)

        """
        from .sprite import offscreen  # noqa: PLC0415 local import to avoid circular dependency

        if fire:
            core, edge, glow = Ball.FIRE_CORE, Ball.FIRE_EDGE, Ball.FIRE_GLOW
        else:
            core, edge, glow = Ball.CORE_COLOR, Ball.EDGE_COLOR, Ball.GLOW_COLOR

        n = 2 * round(radius / PIXEL) * PIXEL // PIXEL  # diameter in art pixels
        size = 2 * (round(radius / PIXEL) * PIXEL + pad)
        sprite, g = offscreen(size, size)
        origin = pad // PIXEL
        mid = (n - 1) / 2
        shades = {"glow": glow, "edge": edge, "body": mix(core, edge, 0.35), "core": core}
        for row in range(-1, n + 1):
            for col in range(-1, n + 1):
                d = math.hypot(col - mid, row - mid)
                if d > mid + 1.3:
                    continue
                if d > mid + 0.5:
                    shade = "glow"
                elif d > mid - 0.6:
                    shade = "edge"
                elif col + row <= mid:
                    shade = "core"
                else:
                    shade = "body"
                g.globalAlpha = 0.35 if shade == "glow" else 1.0
                g.fillStyle = shades[shade]
                block(g, origin + col, origin + row)
        g.globalAlpha = 1.0
        return sprite
