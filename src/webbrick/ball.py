"""A ball in play (several can be in play at once)."""

from __future__ import annotations

import math

from .config import BALL_R, HEIGHT, TRAIL_LEN


class Ball:
    """One ball: position, velocity (px/s), its motion trail, and whether it burns.

    The ball moves itself in ``update()``; the game works out what it ran into
    — a wall, the paddle, a brick — and signals the ball through ``bounce_x()``,
    ``bounce_y()`` and ``bounce_paddle()``, dropping it once ``fallen`` says it
    left the playfield at the bottom.

    ``fire`` is the "pierce" bonus made visible on the ball itself: a burning
    ball smashes through breakable bricks instead of bouncing off them, and
    leaves a fiery trail. The game lights balls up through ``Game.set_balls_fire()``.
    """

    COLOR = "#7dd3fc"  # trail colour while cool
    FIRE_COLOR = "#f97316"  # trail colour while on fire

    __slots__ = ("dx", "dy", "fire", "trail", "x", "y")

    def __init__(self, x: float, y: float, dx: float = 0.0, dy: float = 0.0, *, fire: bool = False) -> None:
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.fire = fire
        self.trail: list[tuple[float, float]] = []

    def update(self, h: float) -> None:
        """Move on for ``h`` seconds, remembering where the ball has been."""
        self.x += self.dx * h
        self.y += self.dy * h
        self.trail.append((self.x, self.y))
        del self.trail[:-TRAIL_LEN]

    @property
    def speed(self) -> float:
        """Distance travelled per second."""
        return math.hypot(self.dx, self.dy)

    @speed.setter
    def speed(self, value: float) -> None:
        """Head at ``value`` px/s along the current heading; a parked ball stays parked."""
        current = self.speed
        if current > 0.0:
            self.dx *= value / current
            self.dy *= value / current

    @property
    def color(self) -> str:
        """The trail colour: the pierce bonus paints the ball fiery."""
        return self.FIRE_COLOR if self.fire else self.COLOR

    @property
    def fallen(self) -> bool:
        """Whether the ball has dropped out below the floor."""
        return self.y - BALL_R > HEIGHT

    def bounce_x(self, x: float) -> None:
        """Bounce off a vertical face, coming to rest at ``x`` (a side wall or a brick)."""
        self.x = x
        self.dx = -self.dx

    def bounce_y(self, y: float) -> None:
        """Bounce off a horizontal face, coming to rest at ``y`` (the ceiling or a brick)."""
        self.y = y
        self.dy = -self.dy

    def bounce_paddle(self, y: float, angle: float, speed: float) -> None:
        """Leave the paddle's face at ``y``, heading ``angle`` from vertical at ``speed`` px/s."""
        self.y = y
        self.head_at(angle, speed)

    def head_at(self, angle: float, speed: float) -> None:
        """Face ``angle`` from straight up, travelling at ``speed`` px/s."""
        self.dx = speed * math.sin(angle)
        self.dy = -speed * math.cos(angle)
