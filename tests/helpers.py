"""Stepping and building helpers shared by several test modules."""

from __future__ import annotations

from typing import TYPE_CHECKING

from webbrick.brick import Brick
from webbrick.config import BALL_R, HEIGHT

if TYPE_CHECKING:
    from webbrick.ball import Ball
    from webbrick.game import Game

FRAME = 1 / 60  # one frame of the animation loop
FALLEN = HEIGHT + BALL_R + 1  # a ball below this has left the playfield


def tick(game: Game, seconds: float) -> None:
    """Advance the simulation in 60 Hz frames."""
    for _ in range(round(seconds / FRAME)):
        game._update(FRAME)


def speed(ball: Ball) -> float:
    return ball.speed


def brick(x: int, y: int, hp: int = 1, *, solid: bool = False, bonus: str | None = None) -> Brick:
    made = Brick(x, y, hp, "#ef4444", solid=solid)
    made.bonus = bonus
    return made
