"""A single brick, and building a level's bricks from its layout."""

from __future__ import annotations

from .config import (
    BRICK_GAP,
    BRICK_H,
    BRICK_TOP,
    BRICK_W,
    ROW_COLORS,
    SIDE_MARGIN,
    STEEL,
)


class Brick:
    """One brick: position, remaining hit points, color and hit flash."""

    __slots__ = ("bonus", "color", "flash", "hp", "solid", "x", "y")

    def __init__(self, x: int, y: int, hp: int, color: str, *, solid: bool) -> None:
        self.x = x
        self.y = y
        self.hp = hp
        self.color = color
        self.solid = solid  # steel: bounces the ball, never breaks
        self.flash = 0.0
        self.bonus: str | None = None  # power-up dropped when it breaks


def build_bricks(rows: tuple[str, ...]) -> list[Brick]:
    """Turn a level layout into a list of bricks."""
    bricks = []
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            if cell == ".":
                continue
            x = SIDE_MARGIN + c * (BRICK_W + BRICK_GAP)
            y = BRICK_TOP + r * (BRICK_H + BRICK_GAP)
            if cell == "X":
                bricks.append(Brick(x, y, 0, STEEL, solid=True))
            else:
                color = ROW_COLORS[r % len(ROW_COLORS)]
                bricks.append(Brick(x, y, int(cell), color, solid=False))
    return bricks
