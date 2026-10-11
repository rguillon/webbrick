"""The browser entry point: it builds the game and hands the loop to the page."""

from __future__ import annotations

import pytest

import webbrick.main as main_module
from webbrick.game import Game


@pytest.mark.usefixtures("window")
def test_main_returns_the_game_it_started() -> None:
    assert isinstance(main_module.main(), Game)


@pytest.mark.usefixtures("window")
def test_main_starts_the_animation_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    callbacks: list[object] = []
    monkeypatch.setattr(main_module, "requestAnimationFrame", callbacks.append)
    started = main_module.main()
    assert callbacks == [started.frame_proxy]
