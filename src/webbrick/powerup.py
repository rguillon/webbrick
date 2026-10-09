"""A bonus capsule falling from a broken brick."""

from __future__ import annotations


class PowerUp:
    """One falling capsule: top-left position and its kind (a ``POWERUPS`` key)."""

    __slots__ = ("kind", "x", "y")

    def __init__(self, x: float, y: float, kind: str) -> None:
        self.x = x
        self.y = y
        self.kind = kind
