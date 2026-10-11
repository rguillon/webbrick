"""Paddle gun: cooldown and bullet spawning."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .bullet import Bullet
from .config import BULLET_H, BULLET_INTERVAL, BULLET_W, PADDLE_W, PADDLE_Y

if TYPE_CHECKING:
    from .paddle import Paddle


class Gun:
    """Manages gun cooldown and creates bullets at paddle ends."""

    def __init__(self) -> None:
        self.cooldown = 0.0

    def update(self, dt: float) -> None:
        """Decrease cooldown."""
        self.cooldown = max(0.0, self.cooldown - dt)

    def try_fire(self, paddle: Paddle) -> list[Bullet] | None:
        """If ready and fire held, spawn two bullets and return them; else None."""
        if self.cooldown == 0:
            self.cooldown = BULLET_INTERVAL
            left_x = paddle.x + 9 - BULLET_W / 2
            right_x = paddle.x + PADDLE_W - 9 - BULLET_W / 2
            y = PADDLE_Y - 6 - BULLET_H
            return [Bullet(left_x, y), Bullet(right_x, y)]
        return None

    def reset(self) -> None:
        """Reset cooldown to ready."""
        self.cooldown = 0.0
