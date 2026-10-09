"""Game flow, input, ball collisions, bullets and a rendering smoke test."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from helpers import FALLEN, FRAME, brick, speed, tick

from webbrick.ball import Ball
from webbrick.config import (
    BALL_R,
    BRICK_H,
    BRICK_W,
    BULLET_INTERVAL,
    CARD_COLS,
    HUD_H,
    LEVEL_BONUS,
    LIVES_START,
    PADDLE_W,
    PADDLE_Y,
    POINTS_PER_HIT,
    POWERUPS,
    STORAGE_KEY,
    TEXT_CACHE_SIZE,
    WIDTH,
)
from webbrick.levels import LEVELS
from webbrick.powerup import PowerUp

if TYPE_CHECKING:
    from collections.abc import Callable

    from conftest import FakeKey, FakeWindow

    from webbrick.brick import Brick
    from webbrick.game import Game

    Press = Callable[..., FakeKey]


def fire_once(game: Game) -> None:
    """Shoot a single volley with an active gun."""
    game._add_bonus("gun")
    game.held.add("fire")
    game._update(FRAME)
    game.held.clear()


def paddle_hit(game: Game, offset: float) -> Ball:
    """Drop a ball on the paddle, ``offset`` from its centre (-1 to 1), and return it after the bounce."""
    x = game.paddle_x + PADDLE_W / 2 * (1 + offset)
    ball = Ball(x, PADDLE_Y - BALL_R - 1, 0, 300)
    game.balls = [ball]
    game._update(FRAME)
    return ball


# -- game flow ---------------------------------------------------------------------


@pytest.fixture
def ready(game: Game) -> Game:
    """Level 1, with the ball waiting on the paddle."""
    game._start_run(0)
    return game


@pytest.fixture
def chosen(game: Game) -> Game:
    """Confirm the second level from the menu."""
    game.selected = 1
    game._confirm()
    return game


def test_starts_on_the_menu(game: Game) -> None:
    assert game.state == "menu"


@pytest.mark.usefixtures("game")
def test_binds_its_listeners_on_window(window: FakeWindow) -> None:
    assert {"keydown", "keyup", "blur", "resize"} <= set(window.listeners)


def test_confirm_from_menu_starts_the_selected_level(chosen: Game) -> None:
    assert (chosen.state, chosen.level) == ("ready", 1)


def test_confirm_from_menu_starts_a_fresh_run(chosen: Game) -> None:
    assert (chosen.lives, chosen.score) == (LIVES_START, 0)


def test_confirm_from_menu_parks_the_ball_on_the_paddle(chosen: Game) -> None:
    ball = chosen.balls[0]
    assert (ball.x, ball.y) == (chosen.paddle_x + PADDLE_W / 2, PADDLE_Y - BALL_R)


def test_ball_rides_the_paddle_until_launch(ready: Game) -> None:
    ready.held.add("right")
    tick(ready, 0.1)
    assert ready.balls[0].x == pytest.approx(ready.paddle_x + PADDLE_W / 2)


def test_confirm_launches_the_ball(ready: Game) -> None:
    ready._confirm()
    assert ready.state == "playing"


def test_launched_ball_goes_up(ready: Game) -> None:
    ready._confirm()
    assert ready.balls[0].dy < 0


def test_launched_ball_has_the_level_speed(ready: Game) -> None:
    ready._confirm()
    assert speed(ready.balls[0]) == pytest.approx(ready._ball_speed())


@pytest.fixture
def paused(playing: Game) -> Game:
    playing._toggle_pause()
    return playing


def test_pause_sets_the_paused_state(paused: Game) -> None:
    assert paused.state == "paused"


def test_pause_freezes_the_simulation(paused: Game) -> None:
    before = (paused.balls[0].x, paused.balls[0].y)
    tick(paused, 0.5)
    assert (paused.balls[0].x, paused.balls[0].y) == before


def test_confirm_resumes_a_paused_game(paused: Game) -> None:
    paused._confirm()
    assert paused.state == "playing"


def test_p_does_nothing_before_launch(ready: Game, press: Press) -> None:
    press("p")
    assert ready.state == "ready"


@pytest.fixture
def cleared(arena: Game) -> Game:
    """Level 1 cleared by breaking its last brick."""
    arena._damage_brick(arena.bricks[0])
    return arena


def test_breaking_the_last_brick_clears_the_level(cleared: Game) -> None:
    assert cleared.state == "cleared"


def test_clearing_a_level_scores_the_bonus(cleared: Game) -> None:
    assert cleared.score == POINTS_PER_HIT + LEVEL_BONUS


def test_clearing_a_level_marks_it_cleared(cleared: Game) -> None:
    assert 0 in cleared.cleared


@pytest.mark.usefixtures("cleared")
def test_clearing_a_level_saves_it(window: FakeWindow) -> None:
    assert window.localStorage.items[STORAGE_KEY] == "0"


def test_confirm_after_clearing_advances_to_the_next_level(cleared: Game) -> None:
    cleared._confirm()
    assert (cleared.state, cleared.level) == ("ready", 1)


@pytest.mark.usefixtures("rising")
def test_ball_breaking_the_last_brick_clears_the_level(arena: Game) -> None:
    arena.bricks = [brick(200, 200)]
    tick(arena, 0.05)
    assert arena.state == "cleared"


@pytest.fixture
def victory(game: Game) -> Game:
    """Clear the last level."""
    game._start_run(len(LEVELS) - 1)
    game.bricks = [brick(10, HUD_H + 10)]
    game._launch()
    game._damage_brick(game.bricks[0])
    return game


def test_clearing_the_last_level_is_victory(victory: Game) -> None:
    assert victory.state == "victory"


def test_confirm_after_victory_opens_the_menu(victory: Game) -> None:
    victory._confirm()
    assert victory.state == "menu"


@pytest.fixture
def ball_lost(playing: Game) -> Game:
    """Drop the only ball out of the playfield."""
    playing.balls = [Ball(200, FALLEN, 0, 300)]
    playing._update(FRAME)
    return playing


def test_losing_the_ball_costs_a_life(ball_lost: Game) -> None:
    assert ball_lost.lives == LIVES_START - 1


def test_losing_the_ball_parks_a_new_one(ball_lost: Game) -> None:
    assert ball_lost.state == "ready"


@pytest.fixture
def game_over(playing: Game) -> Game:
    """Lose the last life."""
    playing.lives = 1
    playing.balls = [Ball(200, FALLEN, 0, 300)]
    playing._update(FRAME)
    return playing


def test_losing_the_last_life_is_game_over(game_over: Game) -> None:
    assert game_over.state == "over"


def test_confirm_after_game_over_restarts_the_level(game_over: Game) -> None:
    game_over._confirm()
    assert game_over.state == "ready"


def test_confirm_after_game_over_starts_a_fresh_run(game_over: Game) -> None:
    game_over._confirm()
    assert (game_over.lives, game_over.score) == (LIVES_START, 0)


@pytest.fixture
def keeper(arena: Game) -> Ball:
    """Return the ball left in play after one of two balls fell out."""
    ball = Ball(240, 300)
    arena.balls = [Ball(100, FALLEN, 0, 300), ball]
    arena._update(FRAME)
    return ball


def test_fallen_ball_is_removed(arena: Game, keeper: Ball) -> None:
    assert arena.balls == [keeper]


@pytest.mark.usefixtures("keeper")
def test_a_ball_falling_while_others_play_costs_nothing(arena: Game) -> None:
    assert (arena.lives, arena.state) == (LIVES_START, "playing")


def test_only_the_last_ball_falling_costs_a_life(arena: Game, keeper: Ball) -> None:
    keeper.y, keeper.dy = FALLEN, 300
    arena._update(FRAME)
    assert (arena.lives, arena.state) == (LIVES_START - 1, "ready")


@pytest.fixture
def reset(arena: Game) -> Game:
    """Every effect active, capsules and bullets in flight, then every ball lost."""
    arena.balls = [Ball(240, 300, 0, -300)]
    for kind in ("pierce", "speed", "gun", "multi"):
        arena._collect(PowerUp(0, 0, kind))
    arena.powerups = [PowerUp(400, 200, "life")]
    arena.bullets = [[200.0, 300.0]]
    for ball in arena.balls:
        ball.y, ball.dy = FALLEN, 300
    arena._update(FRAME)
    return arena


def test_losing_every_ball_costs_a_life(reset: Game) -> None:
    assert reset.state == "ready"


def test_losing_a_life_parks_a_single_ball(reset: Game) -> None:
    assert len(reset.balls) == 1


def test_losing_a_life_drops_capsules_and_bullets(reset: Game) -> None:
    assert (reset.powerups, reset.bullets) == ([], [])


def test_losing_a_life_ends_the_effects(reset: Game) -> None:
    assert (reset.bonuses, reset.speed_mult, reset.balls[0].fire) == ([], 1.0, False)


# -- input ---------------------------------------------------------------------------


@pytest.fixture
def blurred(playing: Game, press: Press, window: FakeWindow) -> Game:
    """Right arrow held down, then the window loses focus."""
    press("ArrowRight", release=False)
    window.listeners["blur"](None)
    return playing


def test_held_keys_move_the_paddle(playing: Game, press: Press) -> None:
    start = playing.paddle_x
    press("ArrowRight", release=False)
    tick(playing, 0.1)
    assert playing.paddle_x > start


def test_blur_releases_held_keys(blurred: Game) -> None:
    assert blurred.held == set()


def test_blur_pauses_the_game(blurred: Game) -> None:
    assert blurred.state == "paused"


def test_blur_on_the_menu_stays_on_the_menu(game: Game, window: FakeWindow) -> None:
    window.listeners["blur"](None)
    assert game.state == "menu"


def test_paddle_stays_on_screen(playing: Game) -> None:
    playing.held.add("left")
    tick(playing, 3)
    assert playing.paddle_x == 0


@pytest.mark.usefixtures("playing")
def test_space_does_not_scroll_the_page(press: Press) -> None:
    assert press(" ", release=False).prevented


def test_space_is_held_as_fire(playing: Game, press: Press) -> None:
    press(" ", release=False)
    assert "fire" in playing.held


def test_releasing_space_stops_fire(playing: Game, press: Press) -> None:
    press(" ")
    assert "fire" not in playing.held


def test_menu_left_wraps_around(game: Game, press: Press) -> None:
    press("ArrowLeft")
    assert game.selected == len(LEVELS) - 1


def test_menu_down_moves_one_row(game: Game, press: Press) -> None:
    press("ArrowDown")
    assert game.selected == CARD_COLS % len(LEVELS)


def test_menu_digit_starts_that_level(game: Game, press: Press) -> None:
    press("2")
    assert (game.state, game.level) == ("ready", 1)


def test_menu_enter_starts_the_selected_level(game: Game, press: Press) -> None:
    press("Enter")
    assert (game.state, game.level) == ("ready", 0)


@pytest.mark.parametrize("key", ["0", str(len(LEVELS) + 1), "x"])
def test_menu_ignores_other_keys(game: Game, press: Press, key: str) -> None:
    press(key)
    assert (game.state, game.selected) == ("menu", 0)


def test_p_pauses(playing: Game, press: Press) -> None:
    press("p")
    assert playing.state == "paused"


def test_escape_opens_the_menu(playing: Game, press: Press) -> None:
    press("Escape")
    assert playing.state == "menu"


def test_r_restarts_the_level(playing: Game, press: Press) -> None:
    press("r")
    assert playing.state == "ready"


def test_r_resets_the_score(playing: Game, press: Press) -> None:
    playing.score = 50
    press("r")
    assert playing.score == 0


def test_key_repeat_does_not_confirm_twice(ready: Game, press: Press) -> None:
    press(" ", repeat=True)
    assert ready.state == "ready"


# -- collisions -----------------------------------------------------------------------


@pytest.fixture
def cornered(arena: Game) -> Ball:
    """Return a ball after one frame of hitting the top-right corner."""
    ball = Ball(WIDTH - BALL_R - 1, HUD_H + BALL_R + 1, 300, -300)
    arena.balls = [ball]
    arena._update(FRAME)
    return ball


@pytest.fixture
def left_wall(arena: Game) -> Ball:
    """Return a ball after one frame of hitting the left wall."""
    ball = Ball(BALL_R + 1, 300, -300, 0)
    arena.balls = [ball]
    arena._update(FRAME)
    return ball


def test_right_wall_bounces(cornered: Ball) -> None:
    assert cornered.dx < 0


def test_right_wall_keeps_the_ball_inside(cornered: Ball) -> None:
    assert cornered.x <= WIDTH - BALL_R


def test_ceiling_bounces(cornered: Ball) -> None:
    assert cornered.dy > 0


def test_ceiling_keeps_the_ball_below_the_hud(cornered: Ball) -> None:
    assert cornered.y >= HUD_H + BALL_R


def test_left_wall_bounces(left_wall: Ball) -> None:
    assert left_wall.dx > 0


def test_left_wall_keeps_the_ball_inside(left_wall: Ball) -> None:
    assert left_wall.x >= BALL_R


@pytest.mark.parametrize("offset", [0.0, 0.9, -0.9])
def test_paddle_sends_the_ball_up(arena: Game, offset: float) -> None:
    assert paddle_hit(arena, offset).dy < 0


@pytest.mark.parametrize("offset", [0.0, 0.9, -0.9])
def test_paddle_bounce_keeps_the_level_speed(arena: Game, offset: float) -> None:
    assert speed(paddle_hit(arena, offset)) == pytest.approx(arena._ball_speed())


@pytest.mark.parametrize(("offset", "direction"), [(0.0, 0), (0.9, 1), (-0.9, -1)])
def test_paddle_bounce_angle_depends_on_where_it_hits(arena: Game, offset: float, direction: int) -> None:
    ball = paddle_hit(arena, offset)
    assert (ball.dx > 1) - (ball.dx < -1) == direction


@pytest.fixture
def tough(arena: Game, rising: Ball) -> Brick:  # noqa: ARG001 - rising is the ball that hits it
    """Return a two-hit brick, after the rising ball has hit it."""
    target = brick(200, 200, hp=2)
    arena.bricks.append(target)
    tick(arena, 0.05)
    return target


def test_ball_damages_a_brick(tough: Brick) -> None:
    assert tough.hp == 1


def test_damaged_brick_stays(arena: Game, tough: Brick) -> None:
    assert tough in arena.bricks


@pytest.mark.usefixtures("tough")
def test_ball_bounces_off_a_brick(rising: Ball) -> None:
    assert rising.dy > 0


@pytest.mark.usefixtures("tough")
def test_hitting_a_brick_scores(arena: Game) -> None:
    assert arena.score == POINTS_PER_HIT


@pytest.fixture
def steel(arena: Game, rising: Ball) -> Brick:  # noqa: ARG001 - rising is the ball that hits it
    """Return a steel brick, after the rising ball has hit it."""
    target = brick(200, 200, hp=0, solid=True)
    arena.bricks.append(target)
    tick(arena, 0.05)
    return target


def test_steel_never_breaks(arena: Game, steel: Brick) -> None:
    assert steel in arena.bricks


@pytest.mark.usefixtures("steel")
def test_ball_bounces_off_steel(rising: Ball) -> None:
    assert rising.dy > 0


@pytest.mark.usefixtures("steel")
def test_steel_does_not_score(arena: Game) -> None:
    assert arena.score == 0


@pytest.fixture
def fast_hit(arena: Game) -> tuple[Brick, Ball]:
    """Run one long frame of a very fast ball into a brick; return both."""
    target = brick(200, 200)
    arena.bricks.append(target)
    ball = Ball(220, 200 + BRICK_H + BALL_R + 1, 0, -3000)
    arena.balls = [ball]
    arena._update(1 / 30)
    return target, ball


def test_fast_ball_breaks_the_brick(arena: Game, fast_hit: tuple[Brick, Ball]) -> None:
    assert fast_hit[0] not in arena.bricks


def test_fast_ball_does_not_tunnel_through_a_brick(fast_hit: tuple[Brick, Ball]) -> None:
    assert fast_hit[1].dy > 0


def test_ball_bounces_sideways_off_a_brick_side(arena: Game) -> None:
    arena.bricks.append(brick(200, 200))
    ball = Ball(200 - BALL_R - 1, 200 + BRICK_H / 2, 300, 0)
    arena.balls = [ball]
    tick(arena, 0.05)
    assert ball.dx < 0


# -- bullets --------------------------------------------------------------------------


@pytest.fixture
def armed(arena: Game) -> Game:
    """``gun`` just collected."""
    arena._collect(PowerUp(0, 0, "gun"))
    return arena


@pytest.fixture
def volley(armed: Game) -> Game:
    """Armed, with fire held for one frame."""
    armed.held.add("fire")
    armed._update(FRAME)
    return armed


def test_gun_does_not_fire_unless_fire_is_held(armed: Game) -> None:
    armed._update(FRAME)
    assert armed.bullets == []


def test_gun_fires_two_bullets(volley: Game) -> None:
    assert len(volley.bullets) == 2


def test_bullets_straddle_the_paddle_centre(volley: Game) -> None:
    left, right = sorted(x for x, _y in volley.bullets)
    assert left < volley.paddle_x + PADDLE_W / 2 < right


def test_gun_cools_down_between_volleys(volley: Game) -> None:
    volley._update(FRAME)
    assert len(volley.bullets) == 2


def test_gun_fires_again_after_its_interval(volley: Game) -> None:
    volley._update(FRAME)
    tick(volley, BULLET_INTERVAL)
    assert len(volley.bullets) == 4


def test_no_gun_no_bullets(arena: Game) -> None:
    arena.held.add("fire")
    tick(arena, 0.5)
    assert arena.bullets == []


@pytest.fixture
def shot(arena: Game) -> tuple[Brick, Brick]:
    """Fire one volley at a two-hit brick with a one-hit one behind it; return both."""
    near, far = brick(90, 400, hp=2), brick(90, 300)
    arena.bricks += [near, far]
    fire_once(arena)
    tick(arena, 0.5)
    return near, far


def test_bullet_damages_the_first_brick_in_its_path(shot: tuple[Brick, Brick]) -> None:
    assert shot[0].hp == 1


def test_bullet_stops_at_the_first_brick(arena: Game, shot: tuple[Brick, Brick]) -> None:
    assert shot[1] in arena.bricks


@pytest.mark.usefixtures("shot")
def test_bullet_hit_scores(arena: Game) -> None:
    assert arena.score == POINTS_PER_HIT


@pytest.fixture
def shot_steel(arena: Game) -> Brick:
    """Fire one volley at a steel brick and return it."""
    target = brick(90, 400, hp=0, solid=True)
    arena.bricks.append(target)
    fire_once(arena)
    tick(arena, 0.5)
    return target


def test_steel_survives_bullets(arena: Game, shot_steel: Brick) -> None:
    assert shot_steel in arena.bricks


def test_steel_absorbs_bullets(arena: Game, shot_steel: Brick) -> None:
    assert all(x > shot_steel.x + BRICK_W for x, _y in arena.bullets)


def test_bullets_leave_through_the_top(arena: Game) -> None:
    fire_once(arena)
    tick(arena, 1.5)
    assert arena.bullets == []


def test_bullet_can_clear_the_level(arena: Game) -> None:
    arena.bricks = [brick(90, 400)]
    arena._add_bonus("gun")
    arena.held.add("fire")
    tick(arena, 0.5)
    assert arena.state == "cleared"


# -- rendering -----------------------------------------------------------------------


@pytest.mark.parametrize("state", ["menu", "ready", "playing", "paused", "over", "cleared", "victory"])
def test_every_state_renders(arena: Game, state: str) -> None:
    arena.state = state
    arena.bricks += [brick(200, 200, hp=3, bonus="multi"), brick(260, 200, hp=0, solid=True)]
    arena.bricks[-1].flash = 0.05
    arena.cleared = {0}
    arena.powerups = [PowerUp(100, 300, kind) for kind in POWERUPS]
    arena.bullets = [[200.0, 300.0]]
    for kind in ("pierce", "speed", "gun"):
        arena._add_bonus(kind)
    arena.balls[0].trail = [(100.0, 100.0), (101.0, 101.0)]
    arena.shake = 0.2
    arena.particles.burst(100, 100, "#ffffff", 5)
    arena.frame(1000.0)
    arena.frame(1016.0)


def test_a_calm_frame_renders(arena: Game) -> None:
    arena._add_bonus("pierce")  # one effect on the HUD, the others off
    arena.frame(1000.0)
    arena.frame(1016.0)


@pytest.fixture
def resized(game: Game, window: FakeWindow) -> float:
    """Halve the pixel ratio and resize; return the scale from before."""
    old = game.scale
    window.devicePixelRatio = 1.0
    window.listeners["resize"](None)
    return old


def test_resize_follows_the_pixel_ratio(game: Game, resized: float) -> None:
    assert game.scale == pytest.approx(resized / 2)


def test_resize_keeps_the_sprites(game: Game, window: FakeWindow) -> None:
    background = game.background
    window.devicePixelRatio = 1.0
    window.listeners["resize"](None)
    assert game.background is background


@pytest.fixture
def full_text_cache(game: Game) -> Game:
    """Fill the text cache to its limit, then draw one more string."""
    for i in range(TEXT_CACHE_SIZE):
        game._text(str(i), 0, 0, "#ffffff")
    game._text("one more", 0, 0, "#ffffff")
    return game


def test_text_cache_is_emptied_when_full(full_text_cache: Game) -> None:
    assert list(full_text_cache._text_sprites) == [("one more", "#ffffff")]


def test_cached_text_is_reused(game: Game) -> None:
    game._text("again", 0, 0, "#ffffff")
    sprite = game._text_sprites["again", "#ffffff"]
    game._text("again", 0, 0, "#ffffff")
    assert game._text_sprites["again", "#ffffff"] is sprite
