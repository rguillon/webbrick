"""The bonuses a caught capsule puts on the game: multi, life, pierce, speed and gun."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pytest
from helpers import brick, speed, tick

from webbrick import game as game_module
from webbrick.ball import Ball
from webbrick.bonus import BONUSES
from webbrick.config import (
    GUN_TIME,
    LIFE_POINTS,
    MAX_LIVES,
    MULTI_SPREAD,
    PIERCE_TIME,
    POINTS_PER_HIT,
    POWERUPS,
    SPEED_BOOST,
    SPEED_TIME,
)
from webbrick.levels import LEVELS
from webbrick.powerup import PowerUp

if TYPE_CHECKING:
    from webbrick.brick import Brick
    from webbrick.game import Game


def test_every_capsule_starts_a_bonus_class() -> None:
    assert set(BONUSES) == set(POWERUPS)


@pytest.fixture
def all_bonus(game: Game, monkeypatch: pytest.MonkeyPatch) -> Game:
    """Start a level with steel, where every breakable brick gets a bonus."""
    monkeypatch.setattr(game_module, "BONUS_CHANCE", 1.0)
    level = next(i for i, (_name, rows) in enumerate(LEVELS) if any("X" in row for row in rows))
    game._start_run(level)
    return game


def test_bonuses_go_only_on_breakable_bricks(all_bonus: Game) -> None:
    assert all((b.bonus is None) == b.solid for b in all_bonus.bricks)


def test_bonuses_are_known_powerups(all_bonus: Game) -> None:
    assert {b.bonus for b in all_bonus.bricks if b.bonus} <= set(POWERUPS)


# -- multi ---------------------------------------------------------------------------


@pytest.fixture
def split(arena: Game) -> list[Ball]:
    """Return the balls after ``multi`` split one heading straight up."""
    arena.balls = [Ball(240, 300, 0, -300)]
    arena._collect(PowerUp(0, 0, "multi"))
    return arena.balls


def test_multi_splits_into_three_balls(split: list[Ball]) -> None:
    assert len(split) == 3


def test_multi_keeps_the_speed(split: list[Ball]) -> None:
    assert [speed(b) for b in split] == pytest.approx([300] * 3)


def test_multi_spreads_the_balls(split: list[Ball]) -> None:
    angles = sorted(math.atan2(b.dx, -b.dy) for b in split)
    assert angles == pytest.approx([-MULTI_SPREAD, 0, MULTI_SPREAD])


def test_multi_without_balls_does_nothing(arena: Game) -> None:
    arena.balls = []
    arena._collect(PowerUp(0, 0, "multi"))
    assert arena.balls == []


def test_split_balls_inherit_the_fire(arena: Game) -> None:
    arena.balls = [Ball(240, 300, 0, -300)]
    arena._collect(PowerUp(0, 0, "pierce"))
    arena._collect(PowerUp(0, 0, "multi"))
    assert all(ball.fire for ball in arena.balls)


# -- life ----------------------------------------------------------------------------


@pytest.fixture
def extra_life(arena: Game) -> Game:
    """Collect a ``life`` with the maximum number of lives."""
    arena.lives = MAX_LIVES
    arena._collect(PowerUp(0, 0, "life"))
    return arena


def test_lives_are_capped(extra_life: Game) -> None:
    assert extra_life.lives == MAX_LIVES


def test_extra_life_is_converted_to_points(extra_life: Game) -> None:
    assert extra_life.score == LIFE_POINTS


# -- pierce ---------------------------------------------------------------------------


@pytest.fixture
def pierced(arena: Game, rising: Ball) -> Brick:
    """Return a three-hit brick, after a piercing ball has gone through it."""
    target = brick(200, 200, hp=3)
    arena.bricks.append(target)
    arena._collect(PowerUp(0, 0, "pierce"))
    tick(arena, 0.1)
    return target


def test_pierce_smashes_through_bricks(arena: Game, pierced: Brick) -> None:
    assert pierced not in arena.bricks


@pytest.mark.usefixtures("pierced")
def test_pierce_does_not_bounce_off_bricks(rising: Ball) -> None:
    assert rising.dy < 0


@pytest.mark.usefixtures("pierced")
def test_pierce_scores_every_hit_point(arena: Game) -> None:
    assert arena.score == 3 * POINTS_PER_HIT


def test_pierce_still_bounces_off_steel(arena: Game, rising: Ball) -> None:
    arena.bricks.append(brick(200, 200, hp=0, solid=True))
    arena._add_bonus("pierce")
    tick(arena, 0.05)
    assert rising.dy > 0


def test_pierce_lasts_its_time(arena: Game) -> None:
    arena._collect(PowerUp(0, 0, "pierce"))
    arena._update_bonuses(PIERCE_TIME - 0.1)
    assert arena.has_bonus("pierce")


def test_pierce_wears_off(arena: Game) -> None:
    arena._collect(PowerUp(0, 0, "pierce"))
    arena._update_bonuses(PIERCE_TIME + 0.1)
    assert not arena.has_bonus("pierce")


def test_pierce_paints_the_ball_fiery(arena: Game) -> None:
    arena._collect(PowerUp(0, 0, "pierce"))
    assert (arena.balls[0].fire, arena.balls[0].color) == (True, Ball.FIRE_COLOR)


def test_pierce_puts_the_balls_out_when_it_is_over(arena: Game) -> None:
    arena._collect(PowerUp(0, 0, "pierce"))
    arena._update_bonuses(PIERCE_TIME + 0.1)
    assert arena.balls[0].fire is False


# -- speed ----------------------------------------------------------------------------


@pytest.fixture
def base_speed(arena: Game) -> float:
    """Return the level's launch speed, before any ``speed`` bonus."""
    return arena._ball_speed()


@pytest.fixture
def boosted(arena: Game, base_speed: float) -> Ball:
    """Return a ball in flight when ``speed`` is collected."""
    ball = Ball(240, 300, 0, -300)
    arena.balls = [ball]
    arena._collect(PowerUp(0, 0, "speed"))
    return ball


def test_speed_boosts_balls_in_flight(boosted: Ball) -> None:
    assert speed(boosted) == pytest.approx(300 * SPEED_BOOST)


@pytest.mark.usefixtures("boosted")
def test_speed_boosts_the_launch_speed(arena: Game, base_speed: float) -> None:
    assert arena._ball_speed() == pytest.approx(base_speed * SPEED_BOOST)


def test_a_second_speed_refreshes_without_stacking(arena: Game, boosted: Ball) -> None:
    arena._collect(PowerUp(0, 0, "speed"))
    assert speed(boosted) == pytest.approx(300 * SPEED_BOOST)


def test_boosting_a_parked_ball_leaves_it_parked(arena: Game) -> None:
    arena._collect(PowerUp(0, 0, "speed"))
    assert arena.balls[0].speed == 0.0


def test_speed_wearing_off_restores_balls_in_flight(arena: Game, boosted: Ball) -> None:
    arena._update_bonuses(SPEED_TIME + 0.1)
    assert speed(boosted) == pytest.approx(300)


@pytest.mark.usefixtures("boosted")
def test_speed_wearing_off_restores_the_launch_speed(arena: Game, base_speed: float) -> None:
    arena._update_bonuses(SPEED_TIME + 0.1)
    assert arena._ball_speed() == pytest.approx(base_speed)


# -- gun ------------------------------------------------------------------------------


@pytest.fixture
def armed(arena: Game) -> Game:
    """``gun`` just collected."""
    arena._collect(PowerUp(0, 0, "gun"))
    return arena


@pytest.fixture
def gun_expired(armed: Game) -> Game:
    """Fire held for the whole gun time."""
    armed.held.add("fire")
    tick(armed, GUN_TIME + 0.1)
    return armed


def test_gun_lasts_its_time(armed: Game) -> None:
    assert armed.bonuses[0].remaining == GUN_TIME


def test_gun_wears_off(gun_expired: Game) -> None:
    assert not gun_expired.has_bonus("gun")


def test_no_more_bullets_once_the_gun_wears_off(gun_expired: Game) -> None:
    fired = len(gun_expired.bullets)
    tick(gun_expired, 1.0)
    assert len(gun_expired.bullets) <= fired


@pytest.mark.parametrize(("kind", "seconds"), [("pierce", PIERCE_TIME), ("speed", SPEED_TIME), ("gun", GUN_TIME)])
def test_a_worn_off_bonus_is_dropped(arena: Game, kind: str, seconds: float) -> None:
    arena._add_bonus(kind)
    arena._update_bonuses(seconds + 0.1)
    assert arena.bonuses == []


def test_bonus_is_over_when_remaining_hits_zero_exactly(arena: Game) -> None:
    """Test the boundary: remaining == 0 means bonus is over."""
    arena._add_bonus("pierce")  # PIERCE_TIME = 10.0
    # First update: remaining = 10.0 - 5.0 = 5.0 (not over)
    arena._update_bonuses(5.0)
    assert arena.has_bonus("pierce")
    # Second update: remaining = 5.0 - 5.0 = 0.0 (should be over)
    arena._update_bonuses(5.0)
    assert not arena.has_bonus("pierce")
