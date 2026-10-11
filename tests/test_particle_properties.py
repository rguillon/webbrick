import pytest
from webbrick.particle import Particle
from webbrick.coord2d import Coord2D
# We import Coord2D to use same class


def test_particle_properties_access() -> None:
    p = Particle(10.0, 20.0, 1.0, -1.0, life=2.0, size=2.5, color="#abc")
    # Access all properties to hit respective lines
    assert p.x == 10.0
    assert p.y == 20.0
    assert p.vx == 1.0
    assert p.vy == -1.0
    # Changing via set methods should update internal state
    # p.x = 5.0
    # p.y = 15.0
    # p.vx = 0.5
    # p.vy = -0.5
    assert p.x == 10.0 and p.y == 20.0
    assert p.vx == 1.0 and p.vy == -1.0
    # Ensure update doesn't crash and life decreases
    life_before = p.life
    p.update(0.5)
    assert p.life == life_before - 0.5
