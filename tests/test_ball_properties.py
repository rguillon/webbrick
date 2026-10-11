import pytest

from webbrick.ball import Ball


def test_ball_set_x() -> None:
    ball = Ball(0.0, 0.0)
    ball.x = 10.0
    assert ball.x == 10.0


def test_ball_set_y() -> None:
    ball = Ball(0.0, 0.0)
    ball.y = 20.0
    assert ball.y == 20.0


def test_ball_set_dx() -> None:
    ball = Ball(0.0, 0.0)
    ball.dx = -5.0
    assert ball.dx == -5.0


def test_ball_set_dy() -> None:
    ball = Ball(0.0, 0.0)
    ball.dy = 3.0
    assert ball.dy == 3.0


def test_ball_speed_setter_doubles_speed() -> None:
    ball = Ball(0.0, 0.0, dx=3.0, dy=4.0)
    old_speed = ball.speed
    ball.speed = old_speed * 2
    assert ball.speed == pytest.approx(old_speed * 2)


def test_ball_speed_setter_preserves_dx_ratio() -> None:
    ball = Ball(0.0, 0.0, dx=3.0, dy=4.0)
    old_dx = ball.dx
    old_speed = ball.speed
    ball.speed = old_speed * 2
    assert ball.dx / ball.speed == pytest.approx(old_dx / old_speed)


def test_ball_speed_setter_preserves_dy_ratio() -> None:
    ball = Ball(0.0, 0.0, dx=3.0, dy=4.0)
    old_dy = ball.dy
    old_speed = ball.speed
    ball.speed = old_speed * 2
    assert ball.dy / ball.speed == pytest.approx(old_dy / old_speed)
