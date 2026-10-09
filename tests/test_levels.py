"""The level layouts: they are all winnable and they all fit the brick grid."""

from __future__ import annotations

import pytest

from webbrick.brick import build_bricks
from webbrick.config import BRICK_COLS
from webbrick.levels import LEVELS

level_names = [name for name, _rows in LEVELS]
level_rows = [rows for _name, rows in LEVELS]


@pytest.mark.parametrize("name", level_names)
def test_level_has_a_name(name: str) -> None:
    assert name


@pytest.mark.parametrize("rows", level_rows, ids=level_names)
def test_level_has_one_to_eight_rows(rows: tuple[str, ...]) -> None:
    assert 1 <= len(rows) <= 8


@pytest.mark.parametrize("rows", level_rows, ids=level_names)
def test_level_rows_fill_the_grid(rows: tuple[str, ...]) -> None:
    assert all(len(row) == BRICK_COLS and set(row) <= set(".123X") for row in rows)


@pytest.mark.parametrize("rows", level_rows, ids=level_names)
def test_level_can_be_cleared(rows: tuple[str, ...]) -> None:
    assert any(not b.solid for b in build_bricks(rows))


def test_no_two_levels_share_a_name() -> None:
    assert len({name for name, _rows in LEVELS}) == len(LEVELS)
