# AGENTS.md

## What this is
A brick‑breaker game written in pure Python that runs in the browser via Pyodide.
There is no build step, no runtime dependencies, and no image assets. The game
logic lives in the `webbrick` package under `src/webbrick/`. The bootstrap page
`index.html` loads Pyodide and the Python modules. Architecture details are in
`CLAUDE.md`.

## Commands
```bash
make install               # uv sync + pre‑commit hooks — do this first
make run                   # serve at http://127.0.0.1:8000/
make check                 # lock file consistency, linter, type‐checker, depcheck
make test                  # run pytest with coverage (requires 100%)
uv run python -m pytest tests/test_game.py -k NAME -q  # focused run
```

## Must not break
- **`src/webbrick/` module changes must update `MODULES` in `index.html`** or browser import fails.
- Keep `tests/` flat – no sub‑directories. Fixtures are in `tests/conftest.py` and helpers in `tests/helpers.py`.
- One assert per test, one `random.Random()` per module, `create_proxy` for all JS callbacks.
- 100 % coverage is enforced – omit `--cov` only for single‑test focus.

## Running the game
- Opening `index.html` via `file://` fails because the page fetches modules from the server. Use `make run` or `HOST=`/`PORT=` overrides.
- The canvas is in `#stage`; resizing maintains aspect ratio. The game stores cleared levels in the browser `localStorage` key `brickbreaker.cleared`; it **must never change**.

## Development workflow
- **Install dependencies**: `make install`. This creates a virtual environment with `uv` and installs pre‑commit hooks.
- **Update lockfile** when adding or changing dependencies: run `uv sync` **before** committing.
- **Lint + type‑check**: `make check` runs `uv lock --locked`, pre‑commit (ruff + ty), and deptry. The repository only allows the `js` and `pyodide.*` imports via `ty`.
- **Format automatically**: ruff is configured with `fix=true`; run `make check` to auto‑format.
- **Run tests**: `make test`. Tests must maintain 100 % coverage (`[tool.coverage.report] fail_under = 100`).
- **Run a single test** (helps debugging): `uv run python -m pytest path/to/test.py -k NAME -q` or `pytest -q <path> -k <partial-name>`.
- **Mutation testing**: `make mutate` – use the produced report for flaky logic.
- **Build wheel**: `make build` (creates a wheel under `dist/`).
- **Documentation**: `make docs` builds and serves MkDocs; `make docs-test` verifies the build.

## Testing quirks
- Tests are run under CPython with `tests/conftest.py` injecting `FakeJs` and `FakeWindow` stubs; importing `webbrick` outside of these stubs will raise ImportError.
- Each test contains **exactly one** `assert`. If more are needed, create a helper or split into multiple tests.
- Fixtures share state via the `Game` fixture; keep them minimal.
- Test names follow the pattern `test_<module>_<scenario>`. Use `pytest -k` to filter.

## Important files & conventions
- `index.html` `MODULES`: list every module under `src/webbrick/`. When adding or renaming a module, update this array.
- `pyproject.toml`: defines dependencies, lockfile rules, ruff, ty, and test configuration. Treat it as the single source of truth for development.
- `Makefile`: contains the canonical build/run/test commands. Do **not** modify it directly; if changes are needed, add to the existing targets.
- `src/webbrick/__init__.py` can stay empty – the package is discovered via the source tree.
- When adding a new module, also add the corresponding documentation block in `docs/modules.md`.
- CI runs `make check`, `make test`, `make docs-test` for Python 3.10–3.14. Coverage is reported to Codecov.

## Known gotchas
- The game runs only inside Pyodide; import errors will occur if you try to run the package normally—use the test stubs instead.
- `make run` uses a simple HTTP server; it cannot serve `file://` paths.
- The `localStorage` key `brickbreaker.cleared` tracks cleared levels; the key **must not** be modified by code.
```
