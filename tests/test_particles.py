"""Every spark on screen at once: throwing bursts, capping them and sweeping them away."""

from __future__ import annotations

from typing import TYPE_CHECKING

from conftest import RecordingCtx

from webbrick.config import MAX_PARTICLES
from webbrick.particles import Particles

if TYPE_CHECKING:
    import random


def test_a_burst_throws_the_asked_number_of_sparks(rng: random.Random) -> None:
    sparks = Particles(rng)
    sparks.burst(100, 100, "#ffffff", 5)
    assert len(sparks) == 5


def test_the_oldest_sparks_are_dropped(rng: random.Random) -> None:
    sparks = Particles(rng)
    sparks.burst(100, 100, "#ffffff", MAX_PARTICLES + 10)
    assert len(sparks) == MAX_PARTICLES


def test_a_burst_starts_every_spark_where_it_was_thrown(rng: random.Random) -> None:
    sparks = Particles(rng)
    sparks.burst(100, 220, "#ffffff", 4)
    assert {(s.x, s.y) for s in sparks} == {(100.0, 220.0)}


def test_burnt_out_sparks_are_dropped(rng: random.Random) -> None:
    sparks = Particles(rng)
    sparks.burst(100, 100, "#ffffff", 5)
    sparks.update(1.0)
    assert len(sparks) == 0


def test_clearing_forgets_every_spark(rng: random.Random) -> None:
    sparks = Particles(rng)
    sparks.burst(100, 100, "#ffffff", 5)
    sparks.clear()
    assert len(sparks) == 0


def test_drawing_gives_the_canvas_its_alpha_back(rng: random.Random) -> None:
    sparks = Particles(rng)
    sparks.burst(100, 100, "#ffffff", 2)
    ctx = RecordingCtx()
    sparks.draw(ctx)
    assert ctx.globalAlpha == 1.0
