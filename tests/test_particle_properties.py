from webbrick.coord2d import Coord2D
from webbrick.particle import Particle


def test_particle_x() -> None:
    p = Particle(Coord2D(10.0, 20.0), Coord2D(1.0, -1.0), life=2.0, size=2.5, color="#abc")
    assert p.x == 10.0


def test_particle_y() -> None:
    p = Particle(Coord2D(10.0, 20.0), Coord2D(1.0, -1.0), life=2.0, size=2.5, color="#abc")
    assert p.y == 20.0


def test_particle_vx() -> None:
    p = Particle(Coord2D(10.0, 20.0), Coord2D(1.0, -1.0), life=2.0, size=2.5, color="#abc")
    assert p.vx == 1.0


def test_particle_vy() -> None:
    p = Particle(Coord2D(10.0, 20.0), Coord2D(1.0, -1.0), life=2.0, size=2.5, color="#abc")
    assert p.vy == -1.0


def test_particle_update_decreases_life() -> None:
    p = Particle(Coord2D(10.0, 20.0), Coord2D(1.0, -1.0), life=2.0, size=2.5, color="#abc")
    life_before = p.life
    p.update(0.5)
    assert p.life == life_before - 0.5
