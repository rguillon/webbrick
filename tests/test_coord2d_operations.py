import pytest

from webbrick.coord2d import Coord2D


def test_coord2d_add() -> None:
    a = Coord2D(3.0, 4.0)
    b = Coord2D(1.0, 2.0)
    c = a + b
    assert (c.x, c.y) == (4.0, 6.0)


def test_coord2d_sub() -> None:
    a = Coord2D(3.0, 4.0)
    b = Coord2D(1.0, 2.0)
    d = a - b
    assert (d.x, d.y) == (2.0, 2.0)


def test_coord2d_mul() -> None:
    a = Coord2D(3.0, 4.0)
    e = a * 2
    assert (e.x, e.y) == (6.0, 8.0)


def test_coord2d_rmul() -> None:
    a = Coord2D(3.0, 4.0)
    f = 3 * a
    assert (f.x, f.y) == (9.0, 12.0)


def test_coord2d_magnitude() -> None:
    a = Coord2D(3.0, 4.0)
    assert a.magnitude() == pytest.approx(5.0)


def test_coord2d_copy_is_new_object() -> None:
    a = Coord2D(3.0, 4.0)
    g = a.copy()
    assert g is not a


def test_coord2d_copy_preserves_values() -> None:
    a = Coord2D(3.0, 4.0)
    g = a.copy()
    assert (g.x, g.y) == (a.x, a.y)


def test_coord2d_iadd() -> None:
    a = Coord2D(3.0, 4.0)
    b = Coord2D(1.0, 2.0)
    a += b
    assert (a.x, a.y) == (4.0, 6.0)


def test_coord2d_isub() -> None:
    a = Coord2D(3.0, 4.0)
    b = Coord2D(1.0, 2.0)
    a -= b
    assert (a.x, a.y) == (2.0, 2.0)
