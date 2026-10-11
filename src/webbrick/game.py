# Copyright (c) 2024-2025 Renaud de Landtsheer
# SPDX-License-Identifier: MIT

"""The game: level-select menu, levels, paddle, ball and bonuses."""

from __future__ import annotations

import math
import random
from random import Random
from typing import TYPE_CHECKING

from js import document, requestAnimationFrame, window
from pyodide.ffi import create_proxy

from .ball import Ball
from .bonus import BONUSES, Bonus
from .brick import Brick, build_bricks
from .bullet import Bullet
from .config import (
    BALL_R,
    BALL_SPEED,
    BALL_SPEED_STEP,
    BONUS_CHANCE,
    BRICK_H,
    BRICK_W,
    BULLET_H,
    BULLET_SPEED,
    BULLET_W,
    CARD_COLS,
    CARD_GAP_X,
    CARD_GAP_Y,
    CARD_H,
    CARD_LEFT,
    CARD_TOP,
    CARD_W,
    CARDS_PER_PAGE,
    CONFIRM_KEYS,
    FLASH_TIME,
    HEIGHT,
    HUD_H,
    LEFT_KEYS,
    LEVEL_BONUS,
    LIFE_POINTS,
    LIVES_START,
    MAX_BALL_STEP,
    MAX_LIVES,
    MAX_TILT,
    MULTI_SPREAD,
    PADDLE_H,
    PADDLE_W,
    PADDLE_Y,
    PIXEL,
    POINTS_PER_HIT,
    POWERUP_FALL_SPEED,
    POWERUP_H,
    POWERUP_W,
    POWERUPS,
    RIGHT_KEYS,
    ROW_COLORS,
    SCROLL_KEYS,
    STAGE_INSET,
    TEXT_CACHE_SIZE,
    WIDTH,
)
from .graphics import (
    make_background,
    make_brick_sprite,
    make_bullet_sprite,
    make_cannon_sprite,
    make_heart_sprite,
    make_paddle_sprite,
    make_powerup_sprite,
    make_preview,
    make_text,
    make_title,
    mix,
    pixel_box,
)
from .gun import Gun
from .levels import LEVELS
from .paddle import Paddle
from .particles import Particles
from .powerup import PowerUp
from .sprite import snap
from .storage import load_cleared, save_cleared

if TYPE_CHECKING:
    from pyodide.ffi import JsProxy

    from .sprite import Sprite


class Game:
    """Brick Breaker: level-select menu, levels, paddle, ball and bonuses."""

    SPRITE_PAD = 12

    def __init__(self) -> None:
        self.canvas = document.getElementById("game")
        self.ctx = self.canvas.getContext("2d")
        self.status = document.getElementById("status")
        self.held: set[str] = set()  # "left" / "right" / "fire"
        self._proxies: list[object] = []  # keep JS<->Python proxies alive
        self._prev_ts = 0.0
        self.t = 0.0  # seconds since start, drives menu animation
        self.rng: Random = random.SystemRandom()

        self.stage = document.getElementById("stage")
        self.scale = 0.0  # device px per logical px; set by _resize()
        self._brick_sprites: dict[tuple[str, int, bool, bool], Sprite] = {}
        self._text_sprites: dict[tuple[str, str], Sprite] = {}
        self.paddle = Paddle()
        self.gun = Gun()
        self._build_sprites()
        self._resize()

        self.cleared = load_cleared()
        self.selected = 0
        self.level = 0
        self.score = 0
        self.lives = LIVES_START
        self.bricks: list[Brick] = []
        self.particles = Particles(self.rng)  # sparks thrown when things break
        self.shake = 0.0
        self.balls: list[Ball] = []
        self.powerups: list[PowerUp] = []  # falling bonus capsules
        self.bonuses: list[Bonus] = []  # running bonus effects, applied on every frame
        self.speed_mult = 1.0  # ball speed multiplier, driven by the "speed" bonus
        self.bullets: list[Bullet | list[float]] = []
        self.state = "menu"  # menu | ready | playing | paused | over | cleared | victory
        self._set_status("Choose a level")
        self.frame_proxy = create_proxy(self.frame)

    # -- game flow -------------------------------------------------------------

    def _open_menu(self) -> None:
        """Return to the level-select menu."""
        self.state = "menu"
        self.selected = self.level
        self.particles.clear()
        self._set_status("Choose a level")

    def _start_run(self, level: int) -> None:
        """Start a fresh run (score 0, full lives) at ``level``."""
        self.score = 0
        self.lives = LIVES_START
        self._start_level(level)

    def _start_level(self, level: int) -> None:
        """Load ``level``'s bricks and put the ball on the paddle."""
        self.level = level
        self.bricks = build_bricks(LEVELS[level][1])
        kinds = list(POWERUPS)
        weights = [weight for _label, _color, weight in POWERUPS.values()]
        for brick in self.bricks:
            if not brick.solid and self.rng.random() < BONUS_CHANCE:
                brick.bonus = self.rng.choices(kinds, weights)[0]
        self.particles.clear()
        self.paddle.reset()
        self.gun.reset()
        self._reset_ball()

    def _reset_ball(self) -> None:
        """Park a single ball on the paddle, waiting for launch; drop active bonuses."""
        self.state = "ready"
        self.balls = [Ball(self.paddle.center_x, self.paddle.ball_bounce_y(BALL_R))]
        self.powerups.clear()
        self.bonuses.clear()
        self.speed_mult = 1.0
        self.bullets.clear()
        self.gun.reset()
        self._set_status(f"Level {self.level + 1} — press Space to launch")

    def _ball_speed(self) -> float:
        return (BALL_SPEED + BALL_SPEED_STEP * self.level) * self.speed_mult

    def _launch(self) -> None:
        """Send the ball off the paddle at a random upward angle."""
        tilt = self.rng.uniform(-MAX_TILT, MAX_TILT) / 2
        self.balls[0].head_at(tilt, self._ball_speed())
        self.state = "playing"
        self._set_status(f"Level {self.level + 1}: {LEVELS[self.level][0]}")

    # Backward compatibility properties for tests
    @property
    def paddle_x(self) -> float:
        """Paddle x position (legacy property for tests)."""
        return self.paddle.x

    @paddle_x.setter
    def paddle_x(self, value: float) -> None:
        self.paddle.x = value

    def _confirm(self) -> None:
        """Space / Enter: the context action for the current state."""
        if self.state == "menu":
            self._start_run(self.selected)
        elif self.state == "ready":
            self._launch()
        elif self.state == "paused":
            self._toggle_pause()
        elif self.state == "over":
            self._start_run(self.level)
        elif self.state == "cleared":
            self._start_level(self.level + 1)
        elif self.state == "victory":
            self._open_menu()

    def _toggle_pause(self) -> None:
        if self.state == "playing":
            self.state = "paused"
            self.held.clear()
            self._set_status("Paused")
        elif self.state == "paused":
            self.state = "playing"
            self._set_status(f"Level {self.level + 1}: {LEVELS[self.level][0]}")

    def _level_cleared(self) -> None:
        """Award the bonus, remember the clear, then advance or finish."""
        self.score += LEVEL_BONUS * (self.level + 1)
        self.cleared.add(self.level)
        save_cleared(self.cleared)
        for _ in range(4):
            self.particles.burst(
                self.rng.uniform(40, WIDTH - 40), self.rng.uniform(120, 360), self.rng.choice(ROW_COLORS), 18
            )
        if self.level == len(LEVELS) - 1:
            self.state = "victory"
            self._set_status("All levels cleared!")
        else:
            self.state = "cleared"
            self._set_status(f"Level {self.level + 1} cleared!")

    def _lose_life(self, x: float) -> None:
        """Count a lost life (the last ball fell at ``x``); end the run at zero lives."""
        self.lives -= 1
        self.shake = 0.35
        self.particles.burst(x, HEIGHT - 4, "#7dd3fc", 24)
        if self.lives <= 0:
            self.state = "over"
            self.balls.clear()
            self.powerups.clear()
            self._set_status("Game over")
        else:
            self._reset_ball()

    # -- update ------------------------------------------------------------------

    def _update(self, dt: float) -> None:
        """Advance the simulation by ``dt`` seconds."""
        self.t += dt
        if self.state == "paused":
            return
        self.shake = max(0.0, self.shake - dt)
        self.particles.update(dt)
        for brick in self.bricks:
            if brick.flash > 0:
                brick.flash = max(0.0, brick.flash - dt)

        if self.state not in ("ready", "playing"):
            return
        self.paddle.update(dt, held_left="left" in self.held, held_right="right" in self.held)

        if self.state == "ready":
            self.balls[0].x = self.paddle.center_x
            return
        self._update_bonuses(dt)
        self._update_powerups(dt)
        self._update_bullets(dt)
        if self.state == "playing":  # a bullet may have cleared the level
            self._update_balls(dt)

    def _update_balls(self, dt: float) -> None:
        """Move every ball in sub-steps, telling it what it hit; the last one out costs a life."""
        for ball in self.balls:
            steps = max(1, math.ceil(ball.speed * dt / MAX_BALL_STEP))
            for _ in range(steps):
                ball.update(dt / steps)
                self._resolve_collisions(ball)
                if self.state != "playing" or ball.fallen:
                    break
            if self.state != "playing":
                return

        # balls that fell out at the bottom are gone; the last one costs a life
        fallen = [ball for ball in self.balls if ball.fallen]
        if fallen:
            self.balls = [ball for ball in self.balls if not ball.fallen]
            if not self.balls:
                self._lose_life(fallen[-1].x)

    def _update_bonuses(self, dt: float) -> None:
        """Apply every running bonus for another ``dt`` seconds; drop the ones that are over."""
        self.bonuses = [bonus for bonus in self.bonuses if not bonus.apply(self, dt)]

    def has_bonus(self, kind: str) -> bool:
        """Return whether a bonus of ``kind`` (a ``POWERUPS`` key) is running."""
        return any(bonus.kind == kind for bonus in self.bonuses)

    def _update_bullets(self, dt: float) -> None:
        """Fire while the gun is active and the fire key is held; move bullets into bricks."""
        self.gun.update(dt)
        if self.has_bonus("gun") and "fire" in self.held:
            new_bullets = self.gun.try_fire(self.paddle)
            if new_bullets:
                self.bullets.extend(new_bullets)
        self.bullets = self._filter_bullets(dt)

    def _filter_bullets(self, dt: float) -> list[Bullet | list[float]]:
        """Update bullets and return those still in play."""
        remaining: list[Bullet | list[float]] = []
        for bullet in self.bullets:
            if isinstance(bullet, Bullet):
                if self._update_new_bullet(bullet, dt, remaining):
                    return []  # level state changed
            elif self._update_legacy_bullet(bullet, dt, remaining):
                return []
        return remaining

    def _update_new_bullet(self, bullet: Bullet, dt: float, remaining: list[Bullet | list[float]]) -> bool:
        """Update a Bullet object. Return True if level state changed."""
        old_y = bullet.y
        bullet.update(dt)
        hit_brick = bullet.check_collision(self.bricks, old_y)
        if hit_brick:
            self.particles.burst(bullet.center_x, hit_brick.y + BRICK_H, "#bef264", 4)
            self._damage_brick(hit_brick)
            return self.state != "playing"
        if not bullet.is_off_screen(old_y):
            remaining.append(bullet)
        return False

    def _update_legacy_bullet(self, bullet: list[float], dt: float, remaining: list[Bullet | list[float]]) -> bool:
        """Update a legacy [x, y] bullet list. Return True if level state changed."""
        x, old_y = bullet
        bullet[1] -= BULLET_SPEED * dt
        top, bottom = bullet[1], old_y + BULLET_H
        hits = [
            b for b in self.bricks if x < b.x + BRICK_W and x + BULLET_W > b.x and top < b.y + BRICK_H and bottom > b.y
        ]
        if hits:
            brick = max(hits, key=lambda b: b.y)
            self.particles.burst(x + BULLET_W / 2, brick.y + BRICK_H, "#bef264", 4)
            self._damage_brick(brick)
            return self.state != "playing"
        if bottom > HUD_H:
            remaining.append(bullet)
        return False

    def set_speed_mult(self, mult: float) -> None:
        """Change the ball speed multiplier, rescaling the balls in flight."""
        ratio = mult / self.speed_mult
        self.speed_mult = mult
        for ball in self.balls:
            ball.speed *= ratio

    def set_balls_fire(self, *, fire: bool) -> None:
        """Light every ball on fire, or put them out; fire balls run through bricks."""
        for ball in self.balls:
            ball.fire = fire

    def set_balls_radius(self, radius: float) -> None:
        """Change the radius of every ball in play."""
        for ball in self.balls:
            ball.radius = radius

    def award_life(self) -> None:
        """Give the player an extra life, or points when they already have the most."""
        if self.lives < MAX_LIVES:
            self.lives += 1
        else:
            self.score += LIFE_POINTS

    def _update_powerups(self, dt: float) -> None:
        """Let bonus capsules fall; the paddle catches them, the floor loses them."""
        remaining = []
        for powerup in self.powerups:
            powerup.y += POWERUP_FALL_SPEED * dt
            if (
                powerup.y + POWERUP_H >= PADDLE_Y
                and powerup.y <= PADDLE_Y + PADDLE_H
                and powerup.x + POWERUP_W >= self.paddle_x
                and powerup.x <= self.paddle_x + PADDLE_W
            ):
                self._collect(powerup)
            elif powerup.y < HEIGHT:
                remaining.append(powerup)
        self.powerups = remaining

    def _collect(self, powerup: PowerUp) -> None:
        """Start the bonus carried by a caught capsule."""
        _label, color, _weight = POWERUPS[powerup.kind]
        self.particles.burst(powerup.x + POWERUP_W / 2, PADDLE_Y, color, 16)
        self._add_bonus(powerup.kind)

    def _add_bonus(self, kind: str) -> None:
        """Run the bonus of ``kind``, replacing one of the same kind that is still running."""
        self.bonuses = [bonus for bonus in self.bonuses if bonus.kind != kind]
        bonus = BONUSES[kind]()
        if not bonus.apply(self, 0.0):  # one-shot bonuses are over as soon as they are applied
            self.bonuses.append(bonus)

    def split_balls(self) -> None:
        """Turn every ball into three, fanned out around its heading."""
        if not self.balls:
            return
        newballs: list[Ball] = []
        for source in self.balls:
            for angle in (-MULTI_SPREAD, MULTI_SPREAD):
                cos, sin = math.cos(angle), math.sin(angle)
                dx = source.dx * cos - source.dy * sin
                dy = source.dx * sin + source.dy * cos
                newballs.append(Ball(source.x, source.y, dx, dy, fire=source.fire))
        self.balls += newballs

    def _resolve_collisions(self, ball: Ball) -> None:
        """Tell ``ball`` what it just ran into: the walls, the paddle, then a brick.

        The ball moves itself; the game only detects and signals.
        """
        r = ball.radius
        if ball.x < r:
            ball.bounce_x(r)
        elif ball.x > WIDTH - r:
            ball.bounce_x(WIDTH - r)
        if ball.y < HUD_H + r:
            ball.bounce_y(HUD_H + r)

        # paddle: bounce angle depends on where the ball struck it
        if (
            ball.dy > 0
            and self.paddle.ball_bounce_y(r) <= ball.y <= PADDLE_Y + PADDLE_H
            and self.paddle.left - r <= ball.x <= self.paddle.right + r
        ):
            offset = self.paddle.ball_hit_offset(ball.x)
            angle = max(-1.0, min(1.0, offset)) * MAX_TILT
            ball.bounce_paddle(self.paddle.ball_bounce_y(r), angle, self._ball_speed())

        self._hit_brick(ball)

    def _hit_brick(self, ball: Ball) -> None:
        """Bounce ``ball`` off the first brick it overlaps and damage it.

        A ball on fire smashes through breakable bricks without bouncing.
        Uses circle-rectangle collision: distance from ball center to the closest
        point on the brick rectangle must be less than ball.radius.
        """
        cx, cy = ball.x, ball.y
        r = ball.radius
        for brick in self.bricks:
            bx, by = brick.x, brick.y
            # Find closest point on brick rectangle to ball center
            closest_x = max(bx, min(cx, bx + BRICK_W))
            closest_y = max(by, min(cy, by + BRICK_H))
            # Vector from closest point to ball center
            dx = cx - closest_x
            dy = cy - closest_y
            dist_sq = dx * dx + dy * dy
            if dist_sq >= r * r:
                continue  # no collision
            if ball.fire and not brick.solid:
                self.score += POINTS_PER_HIT * brick.hp
                self._break_brick(brick)
                return
            # Collision: push ball out to surface and bounce along the normal
            dist = math.sqrt(dist_sq)
            if dist == 0.0:
                # Ball center exactly on rectangle edge/corner; fall back to axis test
                overlap_x = min(cx + r, bx + BRICK_W) - max(cx - r, bx)
                overlap_y = min(cy + r, by + BRICK_H) - max(cy - r, by)
                if overlap_x < overlap_y:
                    ball.bounce_x(bx - r if cx < bx + BRICK_W / 2 else bx + BRICK_W + r)
                else:
                    ball.bounce_y(by - r if cy < by + BRICK_H / 2 else by + BRICK_H + r)
            else:
                # Normalize and push out
                nx = dx / dist
                ny = dy / dist
                ball.pos.x = closest_x + nx * r
                ball.pos.y = closest_y + ny * r
                # Reflect velocity
                dot = ball.vel.x * nx + ball.vel.y * ny
                ball.vel.x -= 2 * dot * nx
                ball.vel.y -= 2 * dot * ny
            self._damage_brick(brick)
            return

    def _damage_brick(self, brick: Brick) -> None:
        """Take one hit point off ``brick`` (steel only flashes)."""
        brick.flash = FLASH_TIME
        if brick.solid:
            return
        brick.hp -= 1
        self.score += POINTS_PER_HIT
        if brick.hp <= 0:
            self._break_brick(brick)

    def _break_brick(self, brick: Brick) -> None:
        """Remove a destroyed brick, drop its bonus and check for a cleared level."""
        self.bricks.remove(brick)
        self.particles.burst(brick.x + BRICK_W / 2, brick.y + BRICK_H / 2, brick.color, 14)
        if brick.bonus is not None:
            self.powerups.append(PowerUp(brick.x + (BRICK_W - POWERUP_W) / 2, brick.y, brick.bonus))
        if not any(not b.solid for b in self.bricks):
            self._level_cleared()

    # -- rendering ---------------------------------------------------------------

    def _resize(self) -> None:  # pragma: no mutate block
        """Fit the canvas to the stage, keeping the playfield's aspect ratio.

        The game always runs in WIDTH x HEIGHT logical units; only the
        backing-store resolution changes. Sprites are pixel art at logical
        resolution, scaled up without smoothing, so they never need redrawing.
        """
        rect = self.stage.getBoundingClientRect() if self.stage is not None else None
        avail_w = rect.width - 2 * STAGE_INSET if rect else WIDTH
        avail_h = rect.height - 2 * STAGE_INSET if rect else HEIGHT
        fit = max(0.25, min(avail_w / WIDTH, avail_h / HEIGHT))
        dpr = window.devicePixelRatio or 1.0
        css_w, css_h = math.floor(WIDTH * fit), math.floor(HEIGHT * fit)
        self.canvas.style.width = f"{css_w}px"
        self.canvas.style.height = f"{css_h}px"
        self.canvas.width = round(css_w * dpr)
        self.canvas.height = round(css_h * dpr)
        self.scale = self.canvas.width / WIDTH

    def _build_sprites(self) -> None:  # pragma: no mutate block
        """Paint the sprites that never change (bricks and text are painted on demand)."""
        self.background = make_background()
        self.paddle_sprite = make_paddle_sprite(self.SPRITE_PAD)
        self.cannon_sprite = make_cannon_sprite(self.SPRITE_PAD)
        self.bullet_sprite: Sprite | None = make_bullet_sprite(self.SPRITE_PAD)
        self.heart_sprite = make_heart_sprite()
        self.title_sprite = make_title("BRICK BREAKER")
        self.powerup_sprites = {kind: make_powerup_sprite(kind, self.SPRITE_PAD) for kind in POWERUPS}
        self.previews = [make_preview(rows) for _, rows in LEVELS]
        # ball sprites by radius
        self._ball_sprites: dict[tuple[float, bool], Sprite] = {}
        self._ball_sprites[(BALL_R, False)] = Ball.make_sprite(self.SPRITE_PAD, BALL_R)
        self._ball_sprites[(BALL_R, True)] = Ball.make_sprite(self.SPRITE_PAD, BALL_R, fire=True)
        # give sprites to paddle and bullet classes
        self.paddle.set_sprites(self.paddle_sprite, self.cannon_sprite)
        Bullet.set_sprite(self.bullet_sprite)

    def _brick_sprite(self, brick: Brick) -> Sprite:
        key = (brick.color, brick.hp, brick.solid, brick.bonus is not None)
        sprite = self._brick_sprites.get(key)
        if sprite is None:
            sprite = make_brick_sprite(brick.color, brick.hp, solid=brick.solid, bonus=key[3])
            self._brick_sprites[key] = sprite
        return sprite

    def _text(self, text: str, pos: tuple[float, float], color: str, *, size: int = 1, align: str = "left") -> float:
        """Draw pixel text ``size`` px per font pixel, vertically centred on ``y``; return its width."""
        x, y = pos
        key = (text, color)
        sprite = self._text_sprites.get(key)
        if sprite is None:
            if len(self._text_sprites) >= TEXT_CACHE_SIZE:
                self._text_sprites.clear()  # changing numbers (score, timers) would pile up
            sprite = self._text_sprites[key] = make_text(text, color)
        w, h = sprite.width * size, sprite.height * size
        if align == "center":
            x -= w / 2
        elif align == "right":
            x -= w
        sprite.draw(self.ctx, round(x), round(y - h / 2), w, h)
        return w

    def _draw(self) -> None:  # pragma: no mutate block
        """Render one frame."""
        ctx = self.ctx
        ctx.setTransform(self.scale, 0, 0, self.scale, 0, 0)
        ctx.imageSmoothingEnabled = False  # resizing the canvas resets it
        self.background.draw(ctx, 0, 0)
        if self.state == "menu":
            self._draw_menu()
            return

        ctx.save()
        if self.shake > 0:
            amp = 8 * self.shake
            ctx.translate(snap(self.rng.uniform(-amp, amp)), snap(self.rng.uniform(-amp, amp)))

        for brick in self.bricks:
            self._brick_sprite(brick).draw(ctx, brick.x, brick.y)
            if brick.flash > 0:
                ctx.globalAlpha = 0.8 * brick.flash / FLASH_TIME
                ctx.fillStyle = "#ffffff"
                ctx.fillRect(brick.x, brick.y, BRICK_W, BRICK_H)
                ctx.globalAlpha = 1.0

        self.particles.draw(ctx)

        self._draw_movers()
        ctx.restore()

        self._draw_hud()
        self._draw_effects()
        self._draw_overlay()

    def _draw_movers(self) -> None:  # pragma: no mutate block
        """Capsules, bullets, the paddle and the balls."""
        ctx = self.ctx
        pad = self.SPRITE_PAD
        for powerup in self.powerups:
            self.powerup_sprites[powerup.kind].draw(ctx, snap(powerup.x) - pad, snap(powerup.y) - pad)
        for bullet in self.bullets:
            if isinstance(bullet, Bullet):
                bullet.draw(ctx, pad)
            else:
                # Backward compatibility: bullet is a [x, y] list
                x, y = bullet
                if self.bullet_sprite:
                    self.bullet_sprite.draw(ctx, snap(x) - pad, snap(y) - pad)
        self.paddle.draw(ctx, pad, has_gun=self.has_bonus("gun"))
        for ball in self.balls:
            ctx.fillStyle = ball.color
            r = ball.radius
            for i, (tx, ty) in enumerate(ball.trail):
                frac = (i + 1) / (len(ball.trail) + 1)
                trail_r = PIXEL * max(1, round(r / PIXEL * frac))
                ctx.globalAlpha = 0.4 * frac
                ctx.beginPath()
                ctx.arc(snap(tx), snap(ty), trail_r, 0, 2 * math.pi)
                ctx.fill()
            ctx.globalAlpha = 1.0
            # Use pixel-based ball sprite for the given radius
            sprite = self._get_ball_sprite(r, fire=ball.fire)
            draw_r = max(BALL_R, round(r / PIXEL) * PIXEL)
            sprite.draw(ctx, snap(ball.x - draw_r) - pad, snap(ball.y - draw_r) - pad)

    def _get_ball_sprite(self, radius: float, *, fire: bool) -> Sprite:
        """Get or create a pixel ball sprite for the given radius and fire state."""
        key = (radius, fire)
        sprite = self._ball_sprites.get(key)
        if sprite is None:
            if fire:
                sprite = Ball.make_sprite(self.SPRITE_PAD, radius, fire=True)
            else:
                sprite = Ball.make_sprite(self.SPRITE_PAD, radius)
            self._ball_sprites[key] = sprite
        return sprite

    def _draw_hud(self) -> None:  # pragma: no mutate block
        ctx = self.ctx
        bands = 4
        for k in range(bands):  # stepped gradient, pixel-art style
            ctx.fillStyle = mix("#1e293b", "#0f172a", k / (bands - 1))
            ctx.fillRect(0, k * HUD_H / bands, WIDTH, HUD_H / bands)
        ctx.fillStyle = "#334155"
        ctx.fillRect(0, HUD_H - PIXEL, WIDTH, PIXEL)

        self._text("Score", (12, 11), "#94a3b8")
        self._text(str(self.score), (12, 27), "#e5e7eb", size=2)
        self._text(f"Level {self.level + 1}", (WIDTH / 2, 11), "#94a3b8", align="center")
        self._text(LEVELS[self.level][0], (WIDTH / 2, 27), "#93c5fd", size=2, align="center")
        heart = self.heart_sprite
        for i in range(self.lives):
            heart.draw(ctx, WIDTH - 24 - i * 16, (HUD_H - heart.height) / 2)

    def _draw_effects(self) -> None:  # pragma: no mutate block
        """Draw the bonuses still running, with their remaining seconds, under the HUD."""
        x = 12
        for bonus in self.bonuses:
            label, color, _weight = POWERUPS[bonus.kind]
            text = f"{label} {math.ceil(bonus.remaining)}s" + (" · hold Space" if bonus.kind == "gun" else "")
            x += self._text(text, (x, HUD_H + 14), color) + 14

    def _draw_overlay(self) -> None:  # pragma: no mutate block
        name = LEVELS[self.level][0]
        panels = {
            "ready": (f"Level {self.level + 1}: {name}", ("Space / Enter: launch", "← → or A / D: move")),
            "paused": ("Paused", ("P or Enter: resume", "Esc: menu")),
            "over": ("Game Over", (f"Score {self.score}", "Enter: retry · Esc: menu")),
            "cleared": ("Level Cleared!", (f"Score {self.score}", "Enter: next · Esc: menu")),
            "victory": ("You beat every level!", (f"Final score {self.score}", "Enter: menu")),
        }
        panel = panels.get(self.state)
        if panel is None:
            return
        title, lines = panel
        top = HEIGHT / 2 - 10
        height = 64 + 22 * len(lines)
        pixel_box(self.ctx, (30, top, WIDTH - 60, height), "rgba(7, 11, 26, 0.85)", "#93c5fd")
        self._text(title, (WIDTH / 2, top + 28), "#93c5fd", size=3, align="center")
        for i, line in enumerate(lines):
            self._text(line, (WIDTH / 2, top + 64 + 22 * i), "#e5e7eb", size=2, align="center")

    def _draw_menu(self) -> None:  # pragma: no mutate block
        ctx = self.ctx
        title = self.title_sprite
        title.draw(ctx, (WIDTH - 4 * title.width) // 2, 72 - 2 * title.height, 4 * title.width, 4 * title.height)
        cleared = f"Select a level · {len(self.cleared)}/{len(LEVELS)} cleared"
        self._text(cleared, (WIDTH / 2, 114), "#93c5fd", size=2, align="center")

        pulse = 0.5 + 0.5 * math.sin(self.t * 5)
        page, pages = self.selected // CARDS_PER_PAGE, -(-len(LEVELS) // CARDS_PER_PAGE)
        self._text(f"← Page {page + 1}/{pages} →", (WIDTH / 2, 134), "#64748b", align="center")
        first = page * CARDS_PER_PAGE
        for i, (name, rows) in enumerate(LEVELS[first : first + CARDS_PER_PAGE], start=first):
            slot = i - first
            x = CARD_LEFT + (slot % CARD_COLS) * (CARD_W + CARD_GAP_X)
            y = CARD_TOP + (slot // CARD_COLS) * (CARD_H + CARD_GAP_Y)
            if i == self.selected:
                border = mix("#38bdf8", "#e0f2fe", round(pulse * 3) / 3)  # pulses in a few steps
                pixel_box(ctx, (x, y, CARD_W, CARD_H), border, border)
                pixel_box(ctx, (x + PIXEL, y + PIXEL, CARD_W - 2 * PIXEL, CARD_H - 2 * PIXEL), "#1e293b", border)
                self._text(f"{i + 1}. {name}", (x + 14, y + 22), "#f8fafc", size=2)
            else:
                pixel_box(ctx, (x, y, CARD_W, CARD_H), "#0f172a", "#334155")
                self._text(f"{i + 1}. {name}", (x + 14, y + 22), "#cbd5e1", size=2)

            preview = self.previews[i]
            preview.draw(ctx, x + (CARD_W - preview.width) // 2, y + 38 + (62 - preview.height) // 2)

            if i in self.cleared:
                self._text("✓ cleared", (x + CARD_W - 12, y + CARD_H - 13), "#4ade80", align="right")
            else:
                self._text(
                    f"{len(build_bricks(rows))} bricks",
                    (x + CARD_W - 12, y + CARD_H - 13),
                    "#64748b",
                    align="right",
                )

        footer = f"Arrows choose · Enter / Space start · 1-{min(9, len(LEVELS))} quick start"
        self._text(footer, (WIDTH / 2, HEIGHT - 14), "#94a3b8", align="center")

    # -- input ---------------------------------------------------------------------

    def bind(self) -> None:
        """Wire up keyboard events (proxies are kept alive)."""
        handlers = (
            ("keydown", self._on_key_down),
            ("keyup", self._on_key_up),
            ("blur", self._on_blur),
            ("resize", self._on_resize),
        )
        for kind, handler in handlers:
            proxy = create_proxy(handler)
            self._proxies.append(proxy)
            window.addEventListener(kind, proxy)

    def _on_key_down(self, event: JsProxy) -> None:
        """Route a key press to the menu or the game."""
        key = event.key
        if key in SCROLL_KEYS:
            event.preventDefault()
        held = self._held_name(key)
        if held is not None:
            self.held.add(held)
        if event.repeat:
            return
        if self.state == "menu":
            self._menu_key(key)
        elif key in CONFIRM_KEYS:
            self._confirm()
        elif key in ("p", "P"):
            self._toggle_pause()
        elif key in ("r", "R"):
            self._start_run(self.level)
        elif key == "Escape":
            self._open_menu()

    def _menu_key(self, key: str) -> None:
        """Move the level selection, or start the chosen level."""
        moves = {"ArrowLeft": -1, "ArrowRight": 1, "ArrowUp": -CARD_COLS, "ArrowDown": CARD_COLS}
        if key in moves:
            self.selected = (self.selected + moves[key]) % len(LEVELS)
        elif key in CONFIRM_KEYS:
            self._confirm()
        elif key.isdigit() and 1 <= int(key) <= len(LEVELS):
            self.selected = int(key) - 1
            self._confirm()

    @staticmethod
    def _held_name(key: str) -> str | None:
        """Return the ``self.held`` name of a key that acts while held down, if any."""
        if key in LEFT_KEYS:
            return "left"
        if key in RIGHT_KEYS:
            return "right"
        if key in CONFIRM_KEYS:
            return "fire"  # shoots while the gun bonus is active
        return None

    def _on_key_up(self, event: JsProxy) -> None:
        """Release a held key."""
        held = self._held_name(event.key)
        if held is not None:
            self.held.discard(held)

    def _on_blur(self, event: JsProxy) -> None:
        """Losing focus drops key-up events: release keys and pause."""
        del event
        self.held.clear()
        if self.state == "playing":
            self._toggle_pause()

    def _on_resize(self, event: JsProxy) -> None:
        """Window resized or zoomed: refit the canvas."""
        del event
        self._resize()

    def _set_status(self, text: str) -> None:
        """Mirror the game state into the page status line."""
        if self.status is not None and self.status.textContent != text:
            self.status.textContent = text

    # -- loop ----------------------------------------------------------------------

    def frame(self, ts: float) -> None:
        """Run one animation-frame tick and schedule the next one."""
        dt = min((ts - self._prev_ts) / 1000.0, 1.0 / 30.0) if self._prev_ts else 0.0
        self._prev_ts = ts
        self._update(dt)
        self._draw()
        requestAnimationFrame(self.frame_proxy)
