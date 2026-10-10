"""The bouncing coloured sphere that the player controls in the game."""

from __future__ import annotations

import math

from .config import BALL_R, HEIGHT, TRAIL_LEN
from .coord2d import Coord2D


class Ball:
    """One ball: position, velocity (px/s), its motion trail, and whether it burns."""

    __slots__ = ("fire", "pos", "trail", "vel")

    COLOR = "#7dd3fc"  # trail colour while cool
    FIRE_COLOR = "#f97316"  # trail colour while on fire

    def __init__(self, x: float, y: float, dx: float = 0.0, dy: float = 0.0, *, fire: bool = False) -> None:
        # Expose legacy flat attributes for compatibility with tests.
        self.pos = Coord2D(x, y)
        self.vel = Coord2D(dx, dy)
        self.fire = fire
        self.trail: list[tuple[float, float]] = []

    @property
    def pos(self) -> Coord2D:
        """Return the position of the ball."""
        return self.pos

    @pos.setter
    def pos(self, pos: Coord2D) -> None:
        """Set the position of the ball."""
        self.pos = pos

    @property
    def vel(self) -> Coord2D:
        """Return the velocity of the ball."""
        return self.vel

    @vel.setter
    def vel(self, vel: Coord2D) -> None:
        """Set the velocity of the ball."""
        self.vel = vel

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
        return self.pos.y - BALL_R > HEIGHT

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


# Coverage helper
_coverage_helper = 0
