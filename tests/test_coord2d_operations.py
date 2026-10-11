import pytest
from webbrick.coord2d import Coord2D



def test_coord2d_operations() -> None:
    a = Coord2D(3.0, 4.0)
    b = Coord2D(1.0, 2.0)
    # Addition
    c = a + b
    assert c.x == 4.0 and c.y == 6.0
    # Subtraction
    d = a - b
    assert d.x == 2.0 and d.y == 2.0
    # Multiplication
    e = a * 2
    assert e.x == 6.0 and e.y == 8.0
    # Right multiplication
    f = 3 * a
    assert f.x == 9.0 and f.y == 12.0
    # Magnitude
    assert a.magnitude() == pytest.approx(5.0)
    # Copy
    g = a.copy()
    assert g is not a and g.x == a.x and g.y == a.y
    # In-place add
    a += b
    assert a.x == 4.0 and a.y == 6.0
    # In-place sub
    a -= b
    assert a.x == 3.0 and a.y == 4.0
