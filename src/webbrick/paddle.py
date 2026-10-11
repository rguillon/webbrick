"""The player's paddle: movement, position and drawing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .config import PADDLE_SPEED, PADDLE_W, PADDLE_Y, WIDTH
from .sprite import snap

if TYPE_CHECKING:
    from pyodide.ffi import JsProxy

    from .sprite import Sprite


class Paddle:
    """Player paddle: horizontal position, movement and rendering."""

    def __init__(self) -> None:
        self.x = (WIDTH - PADDLE_W) / 2.0
        self._paddle_sprite: Sprite | None = None
        self._cannon_sprite: Sprite | None = None

    def set_sprites(self, paddle_sprite: Sprite, cannon_sprite: Sprite | None) -> None:
        """Set the sprites used for drawing."""
        self._paddle_sprite = paddle_sprite
        self._cannon_sprite = cannon_sprite

    def reset(self) -> None:
        """Return paddle to centre."""
        self.x = (WIDTH - PADDLE_W) / 2.0

    def update(self, dt: float, *, held_left: bool, held_right: bool) -> None:
        """Move left/right by ``dt`` seconds, clamped to screen."""
        direction = (1 if held_right else 0) - (1 if held_left else 0)
        self.x += direction * PADDLE_SPEED * dt
        self.x = max(0.0, min(WIDTH - PADDLE_W, self.x))

    def draw(self, ctx: JsProxy, pad: int, *, has_gun: bool) -> None:
        """Draw paddle (and cannon overlay if gun is active)."""
        if self._paddle_sprite is None:
            return
        paddle_x = snap(self.x)
        self._paddle_sprite.draw(ctx, paddle_x - pad, PADDLE_Y - pad)
        if has_gun and self._cannon_sprite is not None:
            self._cannon_sprite.draw(ctx, paddle_x - pad, PADDLE_Y - pad)

    @property
    def left(self) -> float:
        """Left edge of the paddle."""
        return self.x

    @property
    def right(self) -> float:
        """Right edge of the paddle."""
        return self.x + PADDLE_W

    @property
    def center_x(self) -> float:
        """Horizontal centre of the paddle."""
        return self.x + PADDLE_W / 2

    def ball_bounce_y(self, ball_radius: float) -> float:
        """Return the Y position where a ball of ``ball_radius`` rests on the paddle."""
        return PADDLE_Y - ball_radius

    def ball_hit_offset(self, ball_x: float) -> float:
        """Return the normalized hit offset (-1 left edge .. 1 right edge)."""
        return (ball_x - self.center_x) / (PADDLE_W / 2)
