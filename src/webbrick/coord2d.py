"""Utility 2D coordinate dataclass used across the game."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self


@dataclass(slots=True)
class Coord2D:
    """A 2D coordinate with ``x`` and ``y`` components."""

    x: float
    y: float

    def __add__(self, other: Coord2D) -> Coord2D:
        """Add two coordinates together, returning a new Coord2D instance."""
        return Coord2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Coord2D) -> Coord2D:
        """Subtract one coordinate from another, returning a new Coord2D instance."""
        return Coord2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Coord2D:
        """Multiply the coordinate by a scalar, returning a new Coord2D instance."""
        return Coord2D(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__

    def magnitude(self) -> float:
        """Return the magnitude (length) of the vector represented by this Coord2D instance."""
        return (self.x**2 + self.y**2) ** 0.5

    def copy(self) -> Coord2D:
        """Return a new Coord2D instance with the same x and y values."""
        return Coord2D(self.x, self.y)

    def __iadd__(self, other: Coord2D) -> Self:
        """In-place addition of another Coord2D to this one."""
        self.x += other.x
        self.y += other.y
        return self

    def __isub__(self, other: Coord2D) -> Self:
        """In-place subtraction of another Coord2D from this one."""
        self.x -= other.x
        self.y -= other.y
        return self
