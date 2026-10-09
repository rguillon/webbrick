"""The bitmap font: every glyph is the same size and can be painted."""

from __future__ import annotations

import pytest

from webbrick.config import POWERUPS
from webbrick.font import GLYPH_H, GLYPH_W, GLYPHS


@pytest.mark.parametrize("char", sorted(GLYPHS))
def test_glyphs_are_five_by_seven(char: str) -> None:
    rows = GLYPHS[char]
    assert (len(rows), {len(row) for row in rows}) == (GLYPH_H, {GLYPH_W})


def test_every_capsule_label_can_be_painted() -> None:
    labels = "".join(label for label, _color, _weight in POWERUPS.values())
    assert set(labels) <= set(GLYPHS)
