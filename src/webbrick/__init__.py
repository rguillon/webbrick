"""Brick Breaker game logic: pure Python running in the browser via Pyodide.

No hand-written JavaScript and no image assets. The game loop, keyboard input and
every graphic (background, bricks, paddle, ball, particles, menu) are generated in
Python through the Pyodide FFI (``js`` for DOM access, ``create_proxy`` so JS can
call back into Python).

``index.html`` (at the project root) copies this package into Pyodide's virtual filesystem, then calls
:func:`webbrick.main.main`.
"""
