# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A brick breaker game whose game logic is pure Python, running in the browser through Pyodide (v0.27.2, loaded from the jsDelivr CDN). The project has no build step, no dependencies beyond the stdlib, and no test suite or linter config.

## Commands

```bash
make run                                      # serve at http://127.0.0.1:8000/ (HOST=/PORT= override)
PYTHONPATH=src python3 -m webbrick --port 0    # same, without make; port 0 = pick a free port
pip install -e . && webbrick                   # installed console script
python -m compileall -q src                   # quick syntax check
```

To exercise the game outside a browser, put stub `js` and `pyodide.ffi` modules on `PYTHONPATH` (fake `document`/`window`, and a `create_proxy` that returns its argument). Add `src/webbrick/static` to `sys.path`, then `from brickbreaker.main import main; game = main()`. After that, call `game.frame(ts)` and feed key events to `window`'s registered listeners.

You can't open `index.html` from disk (`file://`) because the page `fetch`es the game's Python modules, so always go through the server. The first load needs internet access to download Pyodide.

## Architecture

The project uses a src layout: the `webbrick` package is in `src/webbrick/`, packaged by `pyproject.toml` (hatchling, no runtime dependencies), with the console script `webbrick = webbrick.server:main`. The browser files live in `src/webbrick/static/`, which is the only directory the server exposes, and hatchling ships them inside the wheel.

- **`static/index.html`** holds the only JavaScript, and it's just a bootstrap: it calls `loadPyodide()` and fetches every file listed in its `MODULES` array, in parallel. It writes them into Pyodide's virtual filesystem at `/home/pyodide/brickbreaker/`, then runs `from brickbreaker.main import main; game = main()` and reports progress or errors in `#status`. **When you add, rename or remove a module in `brickbreaker/`, update `MODULES` too**, or the browser import fails. The page is a full-viewport flex column (header, `#stage`, controls panel). The canvas is absolutely positioned inside `#stage` so that its size never changes the stage's own size, which keeps the resize handling free of feedback loops.
- **`static/brickbreaker/`** is the game, a Python package that runs **inside Pyodide only**. It imports `js` and `pyodide.ffi`, so it can't be imported under regular CPython without stubs. Although it ships inside the wheel, it's a static data directory, not part of `webbrick`, so never import it from server code. Modules use relative imports, with one class per file:
  - `config.py`: all layout, tuning and key constants. `levels.py`: `LEVELS` data.
  - `brick.py`: `Brick` plus `build_bricks()`. `sprite.py`: `Sprite` plus `offscreen()`. `storage.py`: `localStorage` helpers.
  - `graphics.py`: the procedural `make_*` sprite painters, `round_rect()` and `mix()`. It has no class.
  - `game.py`: the `Game` class. `main.py`: `main()`, which creates the game, binds input and starts `requestAnimationFrame`.
  - The dependency direction is `config`/`levels` → `brick`/`sprite`/`storage` → `graphics` → `game` → `main`. Keep it acyclic.
  - Every Python callable handed to JS (event handlers, the frame callback) is wrapped in `create_proxy`, and a reference is kept (`self._proxies`, `self._frame_proxy`) so the proxies aren't garbage-collected. New callbacks must follow the same pattern.
  - Input is keyboard-only (no mouse handlers) and is bound on `window`. Held movement keys are normalized into `self.held` (`"left"`/`"right"`) and cleared on `blur`.
  - The state machine is `self.state` ∈ `menu | ready | playing | paused | over | cleared | victory`. `_confirm()` (Space/Enter) holds the per-state action. `_start_run()` resets score and lives, while `_start_level()` only loads bricks, so a run carries over between levels.
  - Levels are ASCII layouts in `LEVELS` (`.` empty, `1`–`3` hit points, `X` unbreakable steel), `BRICK_COLS` characters per row and at most 8 rows (the menu preview and the HUD spacing assume that). A level is cleared when no breakable bricks remain. Cleared levels persist in `localStorage` (`STORAGE_KEY`).
  - The user requires that all graphics are generated in code, with no image assets. Sprites (background, bricks keyed by `(color, hp, solid)`, paddle, ball, menu previews) are pre-rendered once into off-screen canvases and blitted with `drawImage`. This keeps the number of Python→JS FFI calls per frame low, so follow the same pattern for new visuals.
  - Resolution independence: the game always works in `WIDTH`×`HEIGHT` (480×600) logical units. `_resize()` (run at startup and on window `resize`) fits the canvas to `#stage` with the same aspect ratio. It sets the backing store to CSS size × `devicePixelRatio`, and `_draw()` starts with `setTransform(self.scale, …)`. Sprites are re-rendered at the new scale (`offscreen(w, h, scale)` returns a `Sprite`), so always blit through `Sprite.draw()`, which takes logical sizes, never call `drawImage` directly. `shadowBlur` ignores transforms, so multiply it by the scale.
  - Physics is time-based. `frame()` clamps `dt` to 1/30 s, and `_update()` splits ball motion into sub-steps of at most `MAX_BALL_STEP` px so the ball can't tunnel through bricks. Collisions are resolved per sub-step in `_move_ball()` / `_hit_brick()` (one brick per step, bouncing on the axis with the smaller overlap).
  - All layout and tuning values are module-level constants at the top of the file. Brick positions are computed once in `build_bricks()`.
  - `_set_status()` mirrors the game state into the page's `#status` element.
- **`server.py`** is a stdlib `ThreadingHTTPServer` plus a `SimpleHTTPRequestHandler` that serves `STATIC_DIR`. `__main__.py` lets you run it with `python -m webbrick`. `create_server()` returns a bound but not-yet-serving server, which makes it easy to test.
