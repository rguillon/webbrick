"""Colour mixing and the width of a rendered string."""

from __future__ import annotations

import pytest

from webbrick.font import GLYPH_W
from webbrick.graphics import mix, text_width


@pytest.mark.parametrize(
    ("a", "b", "t", "expected"),
    [
        ("#000000", "#ffffff", 0.0, "#000000"),
        ("#000000", "#ffffff", 1.0, "#ffffff"),
        ("#ff0000", "#0000ff", 0.5, "#800080"),
        ("#808080", "#ffffff", 2.0, "#ffffff"),
    ],
)
def test_mix_blends_and_clamps(a: str, b: str, t: float, expected: str) -> None:
    assert mix(a, b, t) == expected


def test_text_width_counts_the_gaps_between_glyphs() -> None:
    assert text_width("AB") == 2 * GLYPH_W + 1
