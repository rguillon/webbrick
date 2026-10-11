"""Player bullets: position, movement and collision."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .config import BRICK_H, BRICK_W, BULLET_H, BULLET_SPEED, BULLET_W, HUD_H
from .sprite import Sprite, snap

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pyodide.ffi import JsProxy

    from .brick import Brick


class Bullet:
    """Single bullet fired by the paddle gun."""

    _sprite: Sprite | None = None  # class-level shared sprite

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    @classmethod
    def set_sprite(cls, sprite: Sprite) -> None:
        """Set the shared sprite for all bullets."""
        cls._sprite = sprite

    def update(self, dt: float) -> None:
        """Move bullet upward."""
        self.y -= BULLET_SPEED * dt

    def check_collision(self, bricks: list[Brick], old_y: float) -> Brick | None:
        """Return the first brick hit between old_y and new y (swept)."""
        top, bottom = self.y, old_y + BULLET_H
        hits = [
            b
            for b in bricks
            if self.x < b.x + BRICK_W and self.x + BULLET_W > b.x and top < b.y + BRICK_H and bottom > b.y
        ]
        if hits:
            return max(hits, key=lambda b: b.y)
        return None

    def is_off_screen(self, old_y: float) -> bool:
        """Return whether the bullet has passed the top HUD."""
        return old_y + BULLET_H <= HUD_H

    def draw(self, ctx: JsProxy, pad: int) -> None:
        """Draw bullet sprite."""
        if self._sprite is None:
            return
        self._sprite.draw(ctx, snap(self.x) - pad, snap(self.y) - pad)

    @staticmethod
    def _as_tuple(bullet: Bullet) -> tuple[float, float]:
        return (bullet.x, bullet.y)

    def __iter__(self) -> Iterator[float]:
        """Allow iteration as (x, y) tuple for backward compatibility."""
        return iter((self.x, self.y))

    @property
    def center_x(self) -> float:
        """Horizontal centre of the bullet."""
        return self.x + BULLET_W / 2
