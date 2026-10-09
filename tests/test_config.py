"""The layout constants still describe a playfield the game can be drawn on."""

from __future__ import annotations

from webbrick.config import (
    BRICK_COLS,
    BRICK_GAP,
    BRICK_TOP,
    BRICK_W,
    HEIGHT,
    HUD_H,
    PADDLE_H,
    PADDLE_Y,
    SIDE_MARGIN,
    WIDTH,
)


def test_the_brick_grid_fills_the_playfield_width() -> None:
    width = 2 * SIDE_MARGIN + BRICK_COLS * BRICK_W + (BRICK_COLS - 1) * BRICK_GAP
    assert width == WIDTH


def test_the_bricks_start_below_the_hud() -> None:
    assert BRICK_TOP > HUD_H


def test_the_paddle_sits_above_the_floor() -> None:
    assert PADDLE_Y + PADDLE_H < HEIGHT
