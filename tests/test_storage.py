"""Remembering cleared levels in ``localStorage``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from webbrick.config import STORAGE_KEY
from webbrick.levels import LEVELS
from webbrick.storage import load_cleared, save_cleared

if TYPE_CHECKING:
    from conftest import FakeWindow


@pytest.mark.usefixtures("window")
def test_nothing_is_cleared_at_first() -> None:
    assert load_cleared() == set()


def test_save_cleared_stores_sorted_indexes(window: FakeWindow) -> None:
    save_cleared({2, 0})
    assert window.localStorage.items[STORAGE_KEY] == "0,2"


@pytest.mark.usefixtures("window")
def test_cleared_levels_round_trip() -> None:
    save_cleared({2, 0})
    assert load_cleared() == {0, 2}


def test_load_cleared_ignores_garbage(window: FakeWindow) -> None:
    window.localStorage.items[STORAGE_KEY] = f"1,x,,{len(LEVELS)},-2"
    assert load_cleared() == {1}


def test_blocked_storage_reads_as_nothing_cleared(window: FakeWindow, monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(key: str) -> str:
        raise RuntimeError(key)

    window.localStorage.items[STORAGE_KEY] = "0"
    monkeypatch.setattr(window.localStorage, "getItem", blocked)
    assert load_cleared() == set()


def test_blocked_storage_saves_nothing(window: FakeWindow, monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(key: str, _value: str) -> None:
        raise RuntimeError(key)

    monkeypatch.setattr(window.localStorage, "setItem", blocked)
    save_cleared({0})
    assert window.localStorage.items == {}
