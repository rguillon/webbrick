"""Off-screen canvases: snapping to the pixel grid and blitting a sprite."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from conftest import FakeJs, RecordingCtx

from webbrick.sprite import Sprite, offscreen, snap

if TYPE_CHECKING:
    from pyodide.ffi import JsProxy


@pytest.mark.parametrize(("value", "snapped"), [(-1.0, 0), (3.0, 4), (4.0, 4), (7.0, 8)])
def test_snap_rounds_to_the_pixel_grid(value: float, snapped: int) -> None:
    assert snap(value) == snapped


def test_a_sprite_keeps_the_logical_size_it_was_made_at() -> None:
    sprite: Sprite = Sprite(FakeJs(), 30.0, 12.0)
    assert (sprite.width, sprite.height) == (30.0, 12.0)


def test_a_sprite_blits_its_whole_canvas() -> None:
    canvas: JsProxy = FakeJs()
    ctx = RecordingCtx()
    Sprite(canvas, 30.0, 12.0).draw(ctx, 4, 8)
    assert ctx.blits == [(canvas, 4, 8, 30.0, 12.0)]


def test_a_sprite_can_be_blitted_at_another_size() -> None:
    canvas: JsProxy = FakeJs()
    ctx = RecordingCtx()
    Sprite(canvas, 30.0, 12.0).draw(ctx, 0, 0, 60.0, 24.0)
    assert ctx.blits == [(canvas, 0, 0, 60.0, 24.0)]


def test_an_offscreen_canvas_is_never_smaller_than_one_pixel() -> None:
    sprite, _ctx = offscreen(0.4, 0.2)
    assert (sprite.canvas.width, sprite.canvas.height) == (1, 1)
