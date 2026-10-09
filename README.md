# webbrick

[![Release](https://img.shields.io/github/v/release/rguillon/webbrick)](https://img.shields.io/github/v/release/rguillon/webbrick)
[![Build status](https://img.shields.io/github/actions/workflow/status/rguillon/webbrick/main.yml?branch=main)](https://github.com/rguillon/webbrick/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/rguillon/webbrick/branch/main/graph/badge.svg)](https://codecov.io/gh/rguillon/webbrick)
[![Commit activity](https://img.shields.io/github/commit-activity/m/rguillon/webbrick)](https://img.shields.io/github/commit-activity/m/rguillon/webbrick)
[![License](https://img.shields.io/github/license/rguillon/webbrick)](https://img.shields.io/github/license/rguillon/webbrick)

A brick breaker game written in pure Python and running in the browser through
[Pyodide](https://pyodide.org/). There is no build step, no image assets (every
graphic is drawn in code) and no hand-written JavaScript beyond a small bootstrap.

- **Github repository**: <https://github.com/rguillon/webbrick/>
- **Documentation** <https://rguillon.github.io/webbrick/>

## Play the game

```bash
make run            # or: make run PORT=9000
```

Then open <http://127.0.0.1:8000/>. This serves the repository root with
`uv run python -m http.server`. `index.html` loads Pyodide from a CDN (internet needed
on the first load) and then the game package from `src/webbrick/`. Opening
`index.html` directly from disk doesn't work, because the page fetches the Python modules.

### Controls

| Key                      | Menu                         | In game                                   |
| ------------------------ | ---------------------------- | ----------------------------------------- |
| **← → ↑ ↓**              | choose a level               | **← →** (or **A D**) move the paddle      |
| **1**–**6**              | start that level             |                                           |
| **Space / Enter**        | start the selected level     | launch the ball, resume, continue; hold to fire with the gun |
| **P**                    |                              | pause                                     |
| **R**                    |                              | restart the level                         |
| **Esc**                  |                              | back to the level menu                    |

### Levels and bonuses

There are six levels. Bricks take one to three hits, and steel bricks never break.
A level is cleared when every breakable brick is gone, and cleared levels are
remembered in the browser's `localStorage`.

Some bricks drop a capsule when they break. Catch it with the paddle:

- **×3** splits the ball into three.
- **FIRE** lets the ball smash through breakable bricks for a while.
- **♥** gives an extra life (or points once lives are full).
- **FAST** speeds the ball up for a while.
- **GUN** puts cannons on the paddle: hold Space to shoot.

You lose a life when the last ball falls out, which also ends any active bonus.

## Development

```bash
make install        # create the virtual environment and install the pre-commit hooks
make check          # lock file, pre-commit (ruff), ty, deptry
make test           # pytest, coverage must stay at 100%
make docs           # serve the documentation (make docs-test builds it strictly)
```

The game lives in `src/webbrick/`:

| Module        | Contents                                                        |
| ------------- | --------------------------------------------------------------- |
| `config.py`   | layout, tuning and key constants                                |
| `levels.py`   | level layouts as ASCII grids                                    |
| `brick.py`, `ball.py`, `powerup.py`, `bonus.py`, `particle.py`, `particles.py` | game objects |
| `sprite.py`   | off-screen canvases rendered at the display's resolution         |
| `storage.py`  | cleared levels in `localStorage`                                |
| `graphics.py` | procedural painters for every sprite                            |
| `game.py`     | the `Game` class: state machine, physics, bonuses, drawing      |
| `main.py`     | browser entry point                                             |

The package imports `js` and `pyodide.ffi`, which only exist inside Pyodide.
The tests (`tests/conftest.py`) replace them with fakes, so the whole game runs
under plain CPython. When you add or rename a module, also update the `MODULES`
list in `index.html`.

---

Repository initiated with [osprey-oss/cookiecutter-uv](https://github.com/osprey-oss/cookiecutter-uv).
