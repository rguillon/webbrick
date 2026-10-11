"""Browser entry point: create the game and start the animation loop."""

from __future__ import annotations

from js import requestAnimationFrame

from .game import Game


def main() -> Game:
    """Start Brick Breaker on the page's ``#game`` canvas.

    Returns:
        The running game. Keep a reference to it so it isn't garbage-collected.

    """
    game = Game()
    game.bind()
    requestAnimationFrame(game.frame_proxy)
    return game
