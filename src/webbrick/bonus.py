"""The bonus effects a caught capsule starts: timed power-ups and one-shot ones."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .config import BALL_R, BIG_BALL_TIME, GUN_TIME, PIERCE_TIME, SPEED_BOOST, SPEED_TIME

if TYPE_CHECKING:
    from .game import Game


class Bonus:
    """An effect a caught capsule puts on the game, until it runs out.

    ``kind`` is the ``POWERUPS`` key of the capsule that started it (its label
    and colour), and ``duration`` how long it lasts in seconds — one-shot
    bonuses last none. The game applies every running bonus on each frame
    through ``apply()`` and drops the ones that are over.
    """

    kind = ""  # a POWERUPS key
    duration = 0.0  # seconds it lasts

    def __init__(self) -> None:
        self.remaining = self.duration

    def apply(self, game: Game, dt: float) -> bool:  # noqa: ARG002 (unused in base, used by subclasses)
        """Put this bonus's effect on ``game`` for ``dt`` seconds; return whether it is over."""
        self.remaining -= dt
        return self.remaining <= 0


class MultiBonus(Bonus):
    """Splits every ball in play into three."""

    kind = "multi"

    def apply(self, game: Game, dt: float) -> bool:
        """Split the balls, then count the bonus down (it is over straight away)."""
        game.split_balls()
        return super().apply(game, dt)


class FireBonus(Bonus):
    """Lights every ball on fire: they smash through breakable bricks."""

    kind = "pierce"
    duration = PIERCE_TIME

    def apply(self, game: Game, dt: float) -> bool:
        """Keep the balls burning, and put them out once the bonus is over."""
        game.set_balls_fire(fire=True)
        if not super().apply(game, dt):
            return False
        game.set_balls_fire(fire=False)
        return True


class LifeBonus(Bonus):
    """Grants an extra life, or points when the player already has the most."""

    kind = "life"

    def apply(self, game: Game, dt: float) -> bool:
        """Hand out a life or points, then count the bonus down (it is over straight away)."""
        game.award_life()
        return super().apply(game, dt)


class SpeedBonus(Bonus):
    """Speeds every ball up, restoring their normal speed when it runs out."""

    kind = "speed"
    duration = SPEED_TIME

    def apply(self, game: Game, dt: float) -> bool:
        """Keep the balls fast, and slow them back down once the bonus is over."""
        game.set_speed_mult(SPEED_BOOST)  # a no-op once the balls are already boosted
        if not super().apply(game, dt):
            return False
        game.set_speed_mult(1.0)
        return True


class GunBonus(Bonus):
    """Arms the paddle with cannons: holding the fire key shoots volleys."""

    kind = "gun"
    duration = GUN_TIME


class BigBallBonus(Bonus):
    """Doubles the size of every ball for the duration."""

    kind = "bigball"
    duration = BIG_BALL_TIME

    def apply(self, game: Game, dt: float) -> bool:
        """Double ball radius, restore when over."""
        game.set_balls_radius(BALL_R * 2)
        if not super().apply(game, dt):
            return False
        game.set_balls_radius(BALL_R)
        return True


# kind: the class a caught capsule of that kind starts
BONUSES: dict[str, type[Bonus]] = {
    "multi": MultiBonus,
    "pierce": FireBonus,
    "life": LifeBonus,
    "speed": SpeedBonus,
    "gun": GunBonus,
    "bigball": BigBallBonus,
}
