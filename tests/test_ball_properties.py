import pytest
from webbrick.ball import Ball



def test_ball_setters() -> None:
    """Verify that setting positional and velocity attributes updates correctly."""
    ball = Ball(0.0, 0.0)
    # Set position
    ball.x = 10.0
    ball.y = 20.0
    # Set velocity
    ball.dx = -5.0
    ball.dy = 3.0
    assert ball.x == 10.0
    assert ball.y == 20.0
    assert ball.dx == -5.0
    assert ball.dy == 3.0


# Verify that the speed setter keeps the heading

def test_ball_speed_setter() -> None:
    ball = Ball(0.0, 0.0, dx=3.0, dy=4.0)
    old_speed = ball.speed
    ball.speed = old_speed * 2
    assert ball.speed == pytest.approx(old_speed * 2)
    # Headings should remain proportional
    old_dx = ball.dx
    old_dy = ball.dy
    old_speed = ball.speed
    ball.speed = old_speed * 2
    assert ball.speed == pytest.approx(old_speed * 2)
    # Headings should remain proportional
    new_ratio_dx = ball.dx / ball.speed
    new_ratio_dy = ball.dy / ball.speed
    assert new_ratio_dx == pytest.approx(old_dx / old_speed)
    assert new_ratio_dy == pytest.approx(old_dy / old_speed)
