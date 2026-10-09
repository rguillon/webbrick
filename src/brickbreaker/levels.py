"""Level layouts.

One string per brick row, ``BRICK_COLS`` characters each: ``.`` empty,
``1``-``3`` breakable brick with that many hit points, ``X`` steel
(unbreakable). A level is cleared when every breakable brick is gone.
"""

from __future__ import annotations

LEVELS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "First Light",
        (
            "..........",
            "1111111111",
            "1111111111",
            "1111111111",
            "1111111111",
        ),
    ),
    (
        "Pyramid",
        (
            "....22....",
            "...2112...",
            "..211112..",
            ".21111112.",
            "2111111112",
        ),
    ),
    (
        "Checkers",
        (
            "2.2.2.2.2.",
            ".1.1.1.1.1",
            "2.2.2.2.2.",
            ".1.1.1.1.1",
            "3.3.3.3.3.",
            ".1.1.1.1.1",
        ),
    ),
    (
        "Fortress",
        (
            "3333333333",
            "3........3",
            "3.222222.3",
            "3.2.11.2.3",
            "3.222222.3",
            "3........3",
        ),
    ),
    (
        "Gatekeeper",
        (
            "1111111111",
            "2222222222",
            "3333333333",
            "XX.XXXX.XX",
            "..........",
            "X...XX...X",
        ),
    ),
    (
        "Invader",
        (
            "..1....1..",
            "...1..1...",
            "..222222..",
            ".22X22X22.",
            "3333333333",
            "3.333333.3",
            "3.3....3.3",
            "...33.33..",
        ),
    ),
)
