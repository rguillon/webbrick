"""Remembering cleared levels in the browser's ``localStorage``."""

from __future__ import annotations

import contextlib

from js import window

from .config import STORAGE_KEY
from .levels import LEVELS


def load_cleared() -> set[int]:
    """Read the set of cleared level indexes from ``localStorage``."""
    try:
        raw = window.localStorage.getItem(STORAGE_KEY)
    except Exception:  # noqa: BLE001 - storage may be blocked (private mode)
        return set()
    if not raw:
        return set()
    parts = str(raw).split(",")
    return {int(p) for p in parts if p.isdigit() and int(p) < len(LEVELS)}


def save_cleared(cleared: set[int]) -> None:
    """Persist the set of cleared level indexes (best effort)."""
    with contextlib.suppress(Exception):  # storage may be blocked (private mode)
        window.localStorage.setItem(STORAGE_KEY, ",".join(map(str, sorted(cleared))))
