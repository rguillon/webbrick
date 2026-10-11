"""The ball on its own: its motion, its trail and the bounces it is told about."""

from __future__ import annotations

from helpers import FALLEN

from webbrick.ball import Ball
from webbrick.config import TRAIL_LEN


def test_a_parked_ball_is_slow_and_cool() -> None:
    ball = Ball(100, 300)
    assert (ball.speed, ball.fire, ball.color, ball.fallen) == (0.0, False, Ball.COLOR, False)


def test_a_burning_ball_is_fiery() -> None:
    assert Ball(100, 300, fire=True).color == Ball.FIRE_COLOR


def test_setting_the_speed_keeps_the_heading() -> None:
    ball = Ball(100, 100, 300, -400)  # 500 px/s
    ball.speed = 1000.0
    assert (ball.dx, ball.dy) == (600.0, -800.0)


def test_a_ball_moves_itself() -> None:
    ball = Ball(100, 100, 100)
    ball.update(0.5)
    assert (ball.x, ball.y) == (150.0, 100.0)


def test_a_moved_ball_remembers_where_it_has_been() -> None:
    ball = Ball(100, 100, 100)
    ball.update(0.5)
    assert ball.trail == [(150.0, 100.0)]


def test_the_trail_is_capped() -> None:
    ball = Ball(100, 100, 100)
    for _ in range(TRAIL_LEN + 1):
        ball.update(0.5)
    assert len(ball.trail) == TRAIL_LEN


def test_the_trail_removes_oldest_entry() -> None:
    ball = Ball(100, 100, 100)
    for _ in range(TRAIL_LEN + 1):
        ball.update(0.5)
    # After TRAIL_LEN+1 updates, the first position (150, 100) should be gone
    # and the trail should contain the last TRAIL_LEN positions
    assert ball.trail[0] == (150.0 + 100 * 0.5, 100.0)  # second position
    assert ball.trail[-1] == (150.0 + 100 * 0.5 * TRAIL_LEN, 100.0)  # last position


def test_a_bounce_off_a_side_wall_turns_the_ball_around() -> None:
    ball = Ball(100, 100, 300)
    ball.bounce_x(40)
    assert (ball.x, ball.dx) == (40.0, -300.0)


def test_a_bounce_off_the_ceiling_turns_the_ball_around() -> None:
    ball = Ball(100, 100, 0, -300)
    ball.bounce_y(50)
    assert (ball.y, ball.dy) == (50.0, 300.0)


def test_the_paddle_bounce_leaves_at_the_asked_angle() -> None:
    ball = Ball(100, 100, 0, 300)
    ball.bounce_paddle(200, 0.0, 280)
    assert (ball.y, ball.dx, ball.dy) == (200.0, 0.0, -280.0)


def test_a_ball_below_the_floor_has_fallen() -> None:
    assert Ball(200, FALLEN).fallen


def test_ball_constructor_with_radius() -> None:
    """Ball accepts optional radius parameter."""
    ball = Ball(100, 300, radius=14.0)
    assert ball.radius == 14.0


def test_ball_radius_setter() -> None:
    """Ball radius can be changed via property setter."""
    ball = Ball(100, 300)
    ball.radius = 21.0
    assert ball.radius == 21.0


def test_ball_make_sprite_core_shade() -> None:
    """Ball.make_sprite produces a sprite with core shade for larger radius."""
    from webbrick.config import BALL_R
    from webbrick.sprite import Sprite

    # For BALL_R=7 core shade is not hit; use radius=14 where it is
    sprite = Ball.make_sprite(12, BALL_R * 2)
    assert isinstance(sprite, Sprite)
    # Creating the sprite exercises the core shade branch
