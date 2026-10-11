"""Bricks, and building a level's bricks from its layout."""

from __future__ import annotations

import pytest

from webbrick.brick import Brick, build_bricks
from webbrick.config import BRICK_GAP, BRICK_H, BRICK_TOP, BRICK_W, ROW_COLORS, SIDE_MARGIN, STEEL


@pytest.fixture
def bricks() -> list[Brick]:
    """Return a one-hit and a three-hit brick on the first row, steel in the middle of the second."""
    return build_bricks(("1.3", ".X."))


def test_build_bricks_reads_the_layout(bricks: list[Brick]) -> None:
    assert [(b.hp, b.solid) for b in bricks] == [(1, False), (3, False), (0, True)]


def test_first_brick_sits_in_the_top_left_corner(bricks: list[Brick]) -> None:
    assert (bricks[0].x, bricks[0].y) == (SIDE_MARGIN, BRICK_TOP)


def test_columns_are_spaced_by_width_and_gap(bricks: list[Brick]) -> None:
    assert bricks[1].x == SIDE_MARGIN + 2 * (BRICK_W + BRICK_GAP)


def test_rows_are_spaced_by_height_and_gap(bricks: list[Brick]) -> None:
    assert bricks[2].y == BRICK_TOP + BRICK_H + BRICK_GAP


def test_steel_brick_x_position_is_computed(bricks: list[Brick]) -> None:
    # steel brick is at column 1 (middle) of row 1
    assert bricks[2].x == SIDE_MARGIN + 1 * (BRICK_W + BRICK_GAP)


def test_bricks_take_their_row_colour(bricks: list[Brick]) -> None:
    assert bricks[0].color == ROW_COLORS[0]


def test_steel_has_its_own_colour(bricks: list[Brick]) -> None:
    assert bricks[2].color == STEEL


def test_built_bricks_start_without_bonus_or_flash(bricks: list[Brick]) -> None:
    assert all(b.bonus is None and b.flash == 0 for b in bricks)
