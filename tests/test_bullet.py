"""Tests for the Bullet class."""

from __future__ import annotations

from webbrick.bullet import Bullet
from webbrick.sprite import Sprite


def make_mock_sprite() -> Sprite:
    """Create a mock sprite for testing."""
    from webbrick.sprite import offscreen

    canvas, _ctx = offscreen(10, 10)
    return Sprite(canvas, 10, 10)


def test_bullet_draw_with_no_sprite() -> None:
    """Bullet.draw returns early when class sprite is not set."""
    Bullet._sprite = None  # type: ignore[assignment]
    try:
        bullet = Bullet(100, 100)

        class MockCtx:
            def fillRect(self, *args: object) -> None:
                pass

            def drawImage(self, *args: object) -> None:
                pass

        bullet.draw(MockCtx(), 0)
    finally:
        Bullet._sprite = None  # type: ignore[assignment]


def test_bullet_draw_with_sprite() -> None:
    """Bullet.draw calls sprite.draw when sprite is set."""
    Bullet._sprite = make_mock_sprite()  # type: ignore[assignment]
    try:
        bullet = Bullet(100, 100)

        class MockCtx:
            def fillRect(self, *args: object) -> None:
                pass

            def drawImage(self, *args: object) -> None:
                pass

        bullet.draw(MockCtx(), 0)
    finally:
        Bullet._sprite = None  # type: ignore[assignment]


def test_bullet_as_tuple() -> None:
    """Bullet._as_tuple returns (x, y)."""
    bullet = Bullet(100, 100)
    assert Bullet._as_tuple(bullet) == (100, 100)


def test_bullet_iter() -> None:
    """Bullet can be iterated as (x, y) tuple."""
    bullet = Bullet(100, 200)
    assert tuple(bullet) == (100, 200)
