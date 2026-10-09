"""Fake browser modules so the Pyodide-only game imports under plain CPython.

``js`` and ``pyodide.ffi`` only exist inside Pyodide, so they are replaced in
``sys.modules`` before any ``webbrick`` module is imported. The fake DOM objects
accept any attribute access or call, which is enough for the drawing code to run.
"""

from __future__ import annotations

import random
import sys
import types
from typing import TYPE_CHECKING

import pytest
from helpers import brick

from webbrick.ball import Ball
from webbrick.config import BALL_R, BRICK_H, HUD_H, WIDTH

if TYPE_CHECKING:
    from collections.abc import Callable

    from webbrick.game import Game


class FakeJs:
    """Stand-in for any JS object: attributes and calls all return fake objects."""

    def __init__(self, **attrs: object) -> None:
        self.__dict__.update(attrs)

    def __getattr__(self, name: str) -> FakeJs:
        if name.startswith("__"):
            raise AttributeError(name)
        value = FakeJs()
        setattr(self, name, value)
        return value

    def __call__(self, *_args: object, **_kwargs: object) -> FakeJs:
        return FakeJs(width=10.0, height=10.0)


class RecordingCtx(FakeJs):
    """A 2D context that remembers the blits and the boxes painted on it."""

    def __init__(self) -> None:
        super().__init__()
        self.blits: list[tuple[object, ...]] = []
        self.boxes: list[tuple[object, ...]] = []

    def drawImage(self, *args: object) -> None:
        self.blits.append(args)

    def fillRect(self, *args: object) -> None:
        self.boxes.append(args)


class FakeStorage:
    """``localStorage`` backed by a dict."""

    def __init__(self) -> None:
        self.items: dict[str, str] = {}

    def getItem(self, key: str) -> str | None:
        return self.items.get(key)

    def setItem(self, key: str, value: str) -> None:
        self.items[key] = value


class FakeWindow:
    """``window``: records event listeners and holds a fake ``localStorage``."""

    devicePixelRatio = 2.0

    def __init__(self) -> None:
        self.listeners: dict[str, Callable[..., None]] = {}
        self.localStorage = FakeStorage()

    def addEventListener(self, kind: str, handler: Callable[..., None]) -> None:
        self.listeners[kind] = handler


class FakeDocument:
    """``document``: a stage of the playfield's size, fake everything else."""

    def __init__(self) -> None:
        self.elements: dict[str, FakeJs] = {
            "stage": FakeJs(getBoundingClientRect=lambda: FakeJs(width=484.0, height=604.0)),
            "status": FakeJs(textContent=""),
        }

    def getElementById(self, element_id: str) -> FakeJs:
        return self.elements.setdefault(element_id, FakeJs())

    def createElement(self, tag: str) -> FakeJs:
        del tag
        return FakeJs()


class FakeKey:
    """A ``KeyboardEvent``."""

    def __init__(self, key: str, *, repeat: bool = False) -> None:
        self.key = key
        self.repeat = repeat
        self.prevented = False

    def preventDefault(self) -> None:
        self.prevented = True


js = types.ModuleType("js")
js.window = FakeWindow()  # ty: ignore[unresolved-attribute]
js.document = FakeDocument()  # ty: ignore[unresolved-attribute]
js.requestAnimationFrame = lambda _callback: None  # ty: ignore[unresolved-attribute]
pyodide = types.ModuleType("pyodide")
ffi = types.ModuleType("pyodide.ffi")
ffi.create_proxy = lambda f: f  # ty: ignore[unresolved-attribute]
pyodide.ffi = ffi  # ty: ignore[unresolved-attribute]
# Keep the stubs from an earlier pytest run in this process (mutmut runs pytest several
# times): the webbrick modules already imported still hold the first ``window``.
for name, module in (("js", js), ("pyodide", pyodide), ("pyodide.ffi", ffi)):
    sys.modules.setdefault(name, module)
js = sys.modules["js"]


@pytest.fixture
def rng() -> random.Random:
    """Return a seeded RNG, so tests draw the same sparks on every run."""
    return random.Random(0)  # noqa: S311 - deterministic gameplay in tests


@pytest.fixture
def window() -> FakeWindow:
    """Return a fresh fake ``window`` (listeners and storage start empty)."""
    js.window.__dict__.clear()
    js.window.__init__()
    return js.window


@pytest.fixture
def game(window: FakeWindow, rng: random.Random) -> Game:  # noqa: ARG001 - window resets js.window before main()
    """Return a started game with a seeded RNG, still on the level menu."""
    from webbrick.main import main  # noqa: PLC0415 - needs the js stubs installed first

    started = main()
    started.rng = rng
    return started


@pytest.fixture
def playing(game: Game) -> Game:
    """Level 1 with the ball launched and no bonus bricks."""
    game._start_run(0)
    for one in game.bricks:
        one.bonus = None
    game._launch()
    return game


@pytest.fixture
def arena(playing: Game) -> Game:
    """Playing, with a single far-off brick (so the level isn't cleared) and a parked ball."""
    playing.bricks = [brick(10, HUD_H + 10)]
    playing.balls = [Ball(WIDTH - 40, 300)]  # zero velocity: stays put
    playing.paddle_x = 100.0
    return playing


@pytest.fixture
def rising(arena: Game) -> Ball:
    """Return a single ball just below the brick at (200, 200), heading up into it."""
    ball = Ball(220, 200 + BRICK_H + BALL_R + 1, 0, -300)
    arena.balls = [ball]
    return ball


@pytest.fixture
def press(window: FakeWindow) -> Callable[..., FakeKey]:
    """Send a key-down (and optionally key-up) through the bound listeners."""

    def send(key: str, *, release: bool = True, repeat: bool = False) -> FakeKey:
        event = FakeKey(key, repeat=repeat)
        window.listeners["keydown"](event)
        if release:
            window.listeners["keyup"](FakeKey(key))
        return event

    return send
