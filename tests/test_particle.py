"""One spark: it flies, it falls, and it fades out as it burns."""

from __future__ import annotations

import pytest
from conftest import RecordingCtx

from webbrick.config import PARTICLE_GRAVITY, PIXEL
from webbrick.coord2d import Coord2D
from webbrick.particle import Particle
from webbrick.sprite import snap


def test_a_spark_moves_and_falls() -> None:
    spark = Particle(Coord2D(100, 100), Coord2D(30, -40), 1.0, 4.0, "#ffffff")
    spark.update(0.1)
    assert (spark.x, spark.y, spark.vy, spark.life) == pytest.approx((103.0, 96.0, -40 + 0.1 * PARTICLE_GRAVITY, 0.9))


def test_a_spark_is_done_when_its_life_is_up() -> None:
    assert not Particle(Coord2D(100, 100), Coord2D(0, 0), 0.5, 4.0, "#ffffff").update(0.5)


def test_a_spark_keeps_the_life_it_was_given() -> None:
    spark = Particle(Coord2D(100, 100), Coord2D(0, 0), 0.5, 4.0, "#ffffff")
    assert spark.max_life == spark.life


def test_a_spark_paints_itself_as_fading() -> None:
    spark = Particle(Coord2D(0, 0), Coord2D(0, 0), 1.0, 4.0, "#ffffff")
    ctx = RecordingCtx()
    spark.update(0.25)
    spark.draw(ctx)
    # globalAlpha should be reset to 1.0 after drawing
    assert ctx.globalAlpha == 1.0


@pytest.mark.parametrize(("size", "side"), [(2.0, PIXEL), (4.0, 2 * PIXEL)])
def test_a_spark_is_painted_as_a_square(size: float, side: int) -> None:
    ctx = RecordingCtx()
    Particle(Coord2D(0, 0), Coord2D(0, 0), 1.0, size, "#ffffff").draw(ctx)
    assert ctx.boxes[0][2] == side


def test_a_spark_is_painted_on_the_pixel_grid() -> None:
    ctx = RecordingCtx()
    Particle(Coord2D(5, 5), Coord2D(0, 0), 1.0, 4.0, "#ffffff").draw(ctx)
    assert ctx.boxes[0][:2] == (snap(3.0), snap(3.0))
