"""Bonus capsules: the brick drops one, it falls, and the paddle catches it."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from helpers import FRAME, brick

from webbrick.config import (
    BRICK_W,
    HEIGHT,
    LIVES_START,
    PADDLE_H,
    PADDLE_W,
    PADDLE_Y,
    POWERUP_FALL_SPEED,
    POWERUP_H,
    POWERUP_W,
)
from webbrick.powerup import PowerUp

if TYPE_CHECKING:
    from webbrick.brick import Brick
    from webbrick.game import Game


def test_a_capsule_keeps_its_place_and_its_kind() -> None:
    capsule = PowerUp(12.5, 30.0, "life")
    assert ((capsule.x, capsule.y), capsule.kind) == ((12.5, 30.0), "life")


@pytest.fixture
def dropped(arena: Game) -> Brick:
    """Break a ``gun`` bonus brick and return it."""
    target = brick(200, 200, bonus="gun")
    arena.bricks.append(target)
    arena._damage_brick(target)
    return target


@pytest.mark.usefixtures("dropped")
def test_breaking_a_bonus_brick_drops_its_capsule(arena: Game) -> None:
    assert [p.kind for p in arena.powerups] == ["gun"]


def test_capsule_drops_from_the_brick_centre(arena: Game, dropped: Brick) -> None:
    capsule = arena.powerups[0]
    assert (capsule.x + POWERUP_W / 2, capsule.y) == (dropped.x + BRICK_W / 2, dropped.y)


@pytest.fixture
def falling(arena: Game) -> Game:
    """One capsule mid-air and one at the bottom edge, half a second later."""
    arena.powerups = [PowerUp(400, 200, "life"), PowerUp(400, HEIGHT - 1, "life")]
    arena._update_powerups(0.5)
    return arena


def test_capsule_falls_slowly_and_is_lost_at_the_bottom(falling: Game) -> None:
    assert [p.y for p in falling.powerups] == [200 + 0.5 * POWERUP_FALL_SPEED]


def test_lost_capsule_has_no_effect(falling: Game) -> None:
    assert falling.lives == LIVES_START


@pytest.fixture
def caught(arena: Game) -> Game:
    """Land a ``life`` capsule on the paddle's edge."""
    arena.powerups = [PowerUp(arena.paddle_x + PADDLE_W - 2, PADDLE_Y - POWERUP_H - 1, "life")]
    arena._update_powerups(0.1)
    return arena


def test_paddle_catches_a_capsule(caught: Game) -> None:
    assert caught.powerups == []


def test_caught_capsule_takes_effect(caught: Game) -> None:
    assert caught.lives == LIVES_START + 1


@pytest.fixture
def missed(arena: Game) -> Game:
    """Let a ``life`` capsule fall below the paddle."""
    arena.powerups = [PowerUp(arena.paddle_x, PADDLE_Y + PADDLE_H + 1, "life")]
    arena._update_powerups(FRAME)
    return arena


def test_capsule_below_the_paddle_is_not_caught(missed: Game) -> None:
    assert len(missed.powerups) == 1


def test_capsule_below_the_paddle_has_no_effect(missed: Game) -> None:
    assert missed.lives == LIVES_START
