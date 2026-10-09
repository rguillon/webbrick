# AGENTS.md

## What this is
A brick-breaker game in pure Python running via Pyodide in the browser. No build step, no runtime dependencies, no image assets. The game is the `webbrick` package in `src/webbrick/`; `index.html` bootstraps Pyodide. Architecture details are in `CLAUDE.md`.

## Commands
```bash
make install               # uv sync + pre-commit hooks — do this first
make run                   # serve at http://127.0.0.1:8000/
make check                 # lock, ruff, ty, deptry
make test                  # pytest with coverage
uv run python -m pytest tests/test_game.py -k NAME -q  # focused run
```

## Must not break
- **`src/webbrick/` module changes must update `MODULES` in `index.html`** or browser import fails
- Keep `tests/` flat — no subdirectories. Fixtures and fakes are in `tests/conftest.py` and `tests/helpers.py`
- One assert per test, one `random.Random()` per module, `create_proxy` for all JS callbacks
- 100% coverage enforced — omit `--cov` for focused runs

## Running the game
- `file://` doesn't work — use `make run`
- `localStorage` key `brickbreaker.cleared` must never change
