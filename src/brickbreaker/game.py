"""The game: level-select menu, levels, paddle, ball and effects."""

from __future__ import annotations

import math
import random
from typing import Any

from js import document, requestAnimationFrame, window
from pyodide.ffi import create_proxy

from .brick import Brick, build_bricks
from .config import (
    BALL_R,
    BALL_SPEED,
    BALL_SPEED_STEP,
    BRICK_H,
    BRICK_W,
    CARD_COLS,
    CARD_GAP_X,
    CARD_GAP_Y,
    CARD_H,
    CARD_LEFT,
    CARD_TOP,
    CARD_W,
    CONFIRM_KEYS,
    FLASH_TIME,
    HEIGHT,
    HUD_H,
    LEFT_KEYS,
    LEVEL_BONUS,
    LIVES_START,
    MAX_BALL_STEP,
    MAX_PARTICLES,
    MAX_TILT,
    PADDLE_H,
    PADDLE_SPEED,
    PADDLE_W,
    PADDLE_Y,
    POINTS_PER_HIT,
    RIGHT_KEYS,
    ROW_COLORS,
    SCROLL_KEYS,
    STAGE_INSET,
    TRAIL_LEN,
    WIDTH,
)
from .graphics import (
    make_background,
    make_ball_sprite,
    make_brick_sprite,
    make_paddle_sprite,
    make_preview,
    round_rect,
)
from .levels import LEVELS
from .sprite import Sprite
from .storage import load_cleared, save_cleared


class Game:
    """Brick Breaker: level-select menu, levels, paddle, ball and effects."""

    SPRITE_PAD = 12

    def __init__(self) -> None:
        self.canvas = document.getElementById("game")
        self.ctx = self.canvas.getContext("2d")
        self.status = document.getElementById("status")
        self.held: set[str] = set()  # "left" / "right"
        self._proxies: list[object] = []  # keep JS<->Python proxies alive
        self._prev_ts = 0.0
        self.t = 0.0  # seconds since start, drives menu animation
        self.rng = random.Random()  # noqa: S311 - gameplay randomness, not security

        self.stage = document.getElementById("stage")
        self.scale = 0.0  # device px per logical px; set by _resize()
        self._brick_sprites: dict[tuple[str, int, bool], Sprite] = {}
        self._resize()

        self.cleared = load_cleared()
        self.selected = 0
        self.level = 0
        self.score = 0
        self.lives = LIVES_START
        self.bricks: list[Brick] = []
        self.particles: list[list[Any]] = []  # [x, y, vx, vy, life, max_life, color, size]
        self.trail: list[tuple[float, float]] = []
        self.shake = 0.0
        self.paddle_x = (WIDTH - PADDLE_W) / 2.0
        self.ball_x = self.ball_y = self.ball_dx = self.ball_dy = 0.0
        self.state = "menu"  # menu | ready | playing | paused | over | cleared | victory
        self._set_status("Choose a level")
        self._frame_proxy = create_proxy(self.frame)

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
        self.particles.clear()
        self.paddle_x = (WIDTH - PADDLE_W) / 2.0
        self._reset_ball()

    def _reset_ball(self) -> None:
        """Park the ball on the paddle, waiting for launch."""
        self.state = "ready"
        self.ball_x = self.paddle_x + PADDLE_W / 2
        self.ball_y = PADDLE_Y - BALL_R
        self.ball_dx = 0.0
        self.ball_dy = 0.0
        self.trail.clear()
        self._set_status(f"Level {self.level + 1} — press Space to launch")

    def _ball_speed(self) -> float:
        return BALL_SPEED + BALL_SPEED_STEP * self.level

    def _launch(self) -> None:
        """Send the ball off the paddle at a random upward angle."""
        tilt = self.rng.uniform(-MAX_TILT, MAX_TILT) / 2
        self.ball_dx = self._ball_speed() * math.sin(tilt)
        self.ball_dy = -self._ball_speed() * math.cos(tilt)
        self.state = "playing"
        self._set_status(f"Level {self.level + 1}: {LEVELS[self.level][0]}")

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
            self._burst(self.rng.uniform(40, WIDTH - 40), self.rng.uniform(120, 360), self.rng.choice(ROW_COLORS), 18)
        if self.level == len(LEVELS) - 1:
            self.state = "victory"
            self._set_status("All levels cleared!")
        else:
            self.state = "cleared"
            self._set_status(f"Level {self.level + 1} cleared!")

    def _lose_life(self) -> None:
        """Count a lost ball; end the run at zero lives."""
        self.lives -= 1
        self.shake = 0.35
        self._burst(self.ball_x, HEIGHT - 4, "#7dd3fc", 24)
        if self.lives <= 0:
            self.state = "over"
            self.trail.clear()
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
        self._update_particles(dt)
        for brick in self.bricks:
            if brick.flash > 0:
                brick.flash = max(0.0, brick.flash - dt)

        if self.state not in ("ready", "playing"):
            return
        direction = ("right" in self.held) - ("left" in self.held)
        self.paddle_x += direction * PADDLE_SPEED * dt
        self.paddle_x = max(0.0, min(WIDTH - PADDLE_W, self.paddle_x))

        if self.state == "ready":
            self.ball_x = self.paddle_x + PADDLE_W / 2  # ball rides the paddle
            return
        self.trail.append((self.ball_x, self.ball_y))
        del self.trail[:-TRAIL_LEN]
        distance = math.hypot(self.ball_dx, self.ball_dy) * dt
        steps = max(1, math.ceil(distance / MAX_BALL_STEP))
        for _ in range(steps):
            self._move_ball(dt / steps)
            if self.state != "playing":  # lost a life or cleared the level
                break

    def _move_ball(self, h: float) -> None:
        """Move the ball by ``h`` seconds and resolve collisions."""
        self.ball_x += self.ball_dx * h
        self.ball_y += self.ball_dy * h

        # walls (the HUD bar is the ceiling)
        if self.ball_x < BALL_R:
            self.ball_x = BALL_R
            self.ball_dx = abs(self.ball_dx)
        elif self.ball_x > WIDTH - BALL_R:
            self.ball_x = WIDTH - BALL_R
            self.ball_dx = -abs(self.ball_dx)
        if self.ball_y < HUD_H + BALL_R:
            self.ball_y = HUD_H + BALL_R
            self.ball_dy = abs(self.ball_dy)

        # paddle: bounce angle depends on where the ball struck it
        if (
            self.ball_dy > 0
            and PADDLE_Y - BALL_R <= self.ball_y <= PADDLE_Y + PADDLE_H
            and self.paddle_x - BALL_R <= self.ball_x <= self.paddle_x + PADDLE_W + BALL_R
        ):
            offset = (self.ball_x - (self.paddle_x + PADDLE_W / 2)) / (PADDLE_W / 2)
            angle = max(-1.0, min(1.0, offset)) * MAX_TILT
            self.ball_dx = self._ball_speed() * math.sin(angle)
            self.ball_dy = -self._ball_speed() * math.cos(angle)
            self.ball_y = PADDLE_Y - BALL_R

        self._hit_brick()

        # fell out at the bottom: lose a life
        if self.state == "playing" and self.ball_y - BALL_R > HEIGHT:
            self._lose_life()

    def _hit_brick(self) -> None:
        """Bounce off the first brick the ball overlaps and damage it."""
        left, right = self.ball_x - BALL_R, self.ball_x + BALL_R
        top, bottom = self.ball_y - BALL_R, self.ball_y + BALL_R
        for brick in self.bricks:
            bx, by = brick.x, brick.y
            if left >= bx + BRICK_W or right <= bx or top >= by + BRICK_H or bottom <= by:
                continue
            # overlapping: bounce on the shallowest axis
            overlap_x = min(right, bx + BRICK_W) - max(left, bx)
            overlap_y = min(bottom, by + BRICK_H) - max(top, by)
            if overlap_x < overlap_y:
                self.ball_dx = -self.ball_dx
                self.ball_x += -overlap_x if self.ball_x < bx + BRICK_W / 2 else overlap_x
            else:
                self.ball_dy = -self.ball_dy
                self.ball_y += -overlap_y if self.ball_y < by + BRICK_H / 2 else overlap_y
            brick.flash = FLASH_TIME
            if brick.solid:
                return
            brick.hp -= 1
            self.score += POINTS_PER_HIT
            if brick.hp <= 0:
                self.bricks.remove(brick)
                self._burst(bx + BRICK_W / 2, by + BRICK_H / 2, brick.color, 14)
                if not any(not b.solid for b in self.bricks):
                    self._level_cleared()
            return

    def _burst(self, x: float, y: float, color: str, count: int) -> None:
        """Spawn a shower of particles at ``(x, y)``."""
        for _ in range(count):
            angle = self.rng.uniform(0, 2 * math.pi)
            speed = self.rng.uniform(60, 220)
            life = self.rng.uniform(0.4, 0.9)
            size = self.rng.uniform(2, 4)
            self.particles.append([x, y, speed * math.cos(angle), speed * math.sin(angle), life, life, color, size])
        del self.particles[:-MAX_PARTICLES]

    def _update_particles(self, dt: float) -> None:
        for p in self.particles:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 420 * dt  # gravity
            p[4] -= dt
        self.particles = [p for p in self.particles if p[4] > 0]

    # -- rendering ---------------------------------------------------------------

    def _resize(self) -> None:
        """Fit the canvas to the stage, keeping the playfield's aspect ratio.

        The game always runs in WIDTH x HEIGHT logical units; only the
        backing-store resolution changes. Sprites are re-rendered at the new
        scale so they stay crisp instead of being upscaled.
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
        scale = self.canvas.width / WIDTH
        if scale == self.scale:
            return
        self.scale = scale
        self.background = make_background(scale)
        self.paddle_sprite = make_paddle_sprite(self.SPRITE_PAD, scale)
        self.ball_sprite = make_ball_sprite(self.SPRITE_PAD, scale)
        self.previews = [make_preview(rows, scale) for _, rows in LEVELS]
        self._brick_sprites.clear()

    def _brick_sprite(self, brick: Brick) -> Sprite:
        key = (brick.color, brick.hp, brick.solid)
        sprite = self._brick_sprites.get(key)
        if sprite is None:
            sprite = make_brick_sprite(brick.color, brick.hp, self.scale, solid=brick.solid)
            self._brick_sprites[key] = sprite
        return sprite

    def _draw(self) -> None:
        """Render one frame."""
        ctx = self.ctx
        ctx.setTransform(self.scale, 0, 0, self.scale, 0, 0)
        self.background.draw(ctx, 0, 0)
        if self.state == "menu":
            self._draw_menu()
            return

        ctx.save()
        if self.shake > 0:
            amp = 8 * self.shake
            ctx.translate(self.rng.uniform(-amp, amp), self.rng.uniform(-amp, amp))

        for brick in self.bricks:
            self._brick_sprite(brick).draw(ctx, brick.x, brick.y)
            if brick.flash > 0:
                ctx.globalAlpha = 0.8 * brick.flash / FLASH_TIME
                ctx.fillStyle = "#ffffff"
                ctx.fillRect(brick.x, brick.y, BRICK_W, BRICK_H)
                ctx.globalAlpha = 1.0

        for x, y, _vx, _vy, life, max_life, color, size in self.particles:
            ctx.globalAlpha = life / max_life
            ctx.fillStyle = color
            ctx.fillRect(x - size / 2, y - size / 2, size, size)
        ctx.globalAlpha = 1.0

        pad = self.SPRITE_PAD
        self.paddle_sprite.draw(ctx, self.paddle_x - pad, PADDLE_Y - pad)
        if self.state in ("ready", "playing", "paused"):
            ball_size = 2 * (BALL_R + pad)
            for i, (tx, ty) in enumerate(self.trail):
                frac = (i + 1) / (len(self.trail) + 1)
                size = ball_size * (0.4 + 0.5 * frac)
                ctx.globalAlpha = 0.35 * frac
                self.ball_sprite.draw(ctx, tx - size / 2, ty - size / 2, size, size)
            ctx.globalAlpha = 1.0
            self.ball_sprite.draw(ctx, self.ball_x - BALL_R - pad, self.ball_y - BALL_R - pad)
        ctx.restore()

        self._draw_hud()
        self._draw_overlay()

    def _draw_hud(self) -> None:
        ctx = self.ctx
        grad = ctx.createLinearGradient(0, 0, 0, HUD_H)
        grad.addColorStop(0, "#1e293b")
        grad.addColorStop(1, "#0f172a")
        ctx.fillStyle = grad
        ctx.fillRect(0, 0, WIDTH, HUD_H)
        ctx.fillStyle = "#334155"
        ctx.fillRect(0, HUD_H - 1, WIDTH, 1)

        ctx.textBaseline = "middle"
        ctx.font = "bold 15px system-ui"
        ctx.fillStyle = "#e5e7eb"
        ctx.textAlign = "left"
        ctx.fillText(f"Score {self.score}", 12, HUD_H / 2)
        ctx.textAlign = "center"
        ctx.fillStyle = "#93c5fd"
        ctx.fillText(f"Level {self.level + 1} · {LEVELS[self.level][0]}", WIDTH / 2, HUD_H / 2)

        # lives as little balls
        ctx.fillStyle = "#7dd3fc"
        for i in range(self.lives):
            ctx.beginPath()
            ctx.arc(WIDTH - 16 - i * 16, HUD_H / 2, 5, 0, 2 * math.pi)
            ctx.fill()

    def _draw_overlay(self) -> None:
        name = LEVELS[self.level][0]
        panels = {
            "ready": (f"Level {self.level + 1}: {name}", ("Space / Enter to launch", "← → or A / D to move")),
            "paused": ("Paused", ("P or Enter to resume", "Esc for the menu")),
            "over": ("Game Over", (f"Score {self.score}", "Enter to retry · Esc for the menu")),
            "cleared": ("Level Cleared!", (f"Score {self.score}", "Enter for the next level · Esc for the menu")),
            "victory": ("You beat every level!", (f"Final score {self.score}", "Enter to return to the menu")),
        }
        panel = panels.get(self.state)
        if panel is None:
            return
        title, lines = panel
        ctx = self.ctx
        top = HEIGHT / 2 - 10
        height = 54 + 22 * len(lines)
        ctx.fillStyle = "rgba(7, 11, 26, 0.82)"
        round_rect(ctx, 30, top, WIDTH - 60, height, 12)
        ctx.fill()
        ctx.strokeStyle = "rgba(147, 197, 253, 0.5)"
        ctx.lineWidth = 1.5
        ctx.stroke()

        ctx.textAlign = "center"
        ctx.textBaseline = "middle"
        ctx.fillStyle = "#93c5fd"
        ctx.font = "bold 20px system-ui"
        ctx.fillText(title, WIDTH / 2, top + 28)
        ctx.fillStyle = "#e5e7eb"
        ctx.font = "14px system-ui"
        for i, line in enumerate(lines):
            ctx.fillText(line, WIDTH / 2, top + 60 + 22 * i)

    def _draw_menu(self) -> None:
        ctx = self.ctx
        ctx.textAlign = "center"
        ctx.textBaseline = "middle"

        # title with a gradient fill and glow
        grad = ctx.createLinearGradient(80, 0, WIDTH - 80, 0)
        for i, color in enumerate(ROW_COLORS):
            grad.addColorStop(i / (len(ROW_COLORS) - 1), color)
        ctx.font = "bold 42px system-ui"
        ctx.shadowColor = "rgba(147, 197, 253, 0.6)"
        ctx.shadowBlur = 18 * self.scale
        ctx.fillStyle = grad
        ctx.fillText("BRICK BREAKER", WIDTH / 2, 72)
        ctx.shadowBlur = 0
        ctx.fillStyle = "#93c5fd"
        ctx.font = "15px system-ui"
        ctx.fillText(f"Select a level  ·  {len(self.cleared)}/{len(LEVELS)} cleared", WIDTH / 2, 114)

        pulse = 0.5 + 0.5 * math.sin(self.t * 5)
        for i, (name, rows) in enumerate(LEVELS):
            x = CARD_LEFT + (i % CARD_COLS) * (CARD_W + CARD_GAP_X)
            y = CARD_TOP + (i // CARD_COLS) * (CARD_H + CARD_GAP_Y)
            selected = i == self.selected
            ctx.fillStyle = "rgba(30, 41, 59, 0.92)" if selected else "rgba(15, 23, 42, 0.8)"
            round_rect(ctx, x, y, CARD_W, CARD_H, 10)
            ctx.fill()
            if selected:
                ctx.shadowColor = "#38bdf8"
                ctx.shadowBlur = (8 + 10 * pulse) * self.scale
                ctx.strokeStyle = "#38bdf8"
                ctx.lineWidth = 2.5
            else:
                ctx.strokeStyle = "#334155"
                ctx.lineWidth = 1
            ctx.stroke()
            ctx.shadowBlur = 0

            ctx.fillStyle = "#f8fafc" if selected else "#cbd5e1"
            ctx.font = "bold 15px system-ui"
            ctx.textAlign = "left"
            ctx.fillText(f"{i + 1}. {name}", x + 14, y + 22)

            preview = self.previews[i]
            preview.draw(ctx, x + (CARD_W - preview.width) / 2, y + 38 + (62 - preview.height) / 2)

            ctx.font = "12px system-ui"
            ctx.textAlign = "right"
            if i in self.cleared:
                ctx.fillStyle = "#4ade80"
                ctx.fillText("✓ cleared", x + CARD_W - 12, y + CARD_H - 13)
            else:
                ctx.fillStyle = "#64748b"
                ctx.fillText(f"{len(build_bricks(rows))} bricks", x + CARD_W - 12, y + CARD_H - 13)

        ctx.textAlign = "center"
        ctx.fillStyle = "#94a3b8"
        ctx.font = "13px system-ui"
        ctx.fillText(
            f"Arrows choose  ·  Enter / Space start  ·  1-{len(LEVELS)} quick start",
            WIDTH / 2,
            HEIGHT - 14,
        )

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

    def _on_key_down(self, event: Any) -> None:
        """Route a key press to the menu or the game."""
        key = event.key
        if key in SCROLL_KEYS:
            event.preventDefault()
        if key in LEFT_KEYS:
            self.held.add("left")
        elif key in RIGHT_KEYS:
            self.held.add("right")
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

    def _on_key_up(self, event: Any) -> None:
        """Release a held paddle key."""
        if event.key in LEFT_KEYS:
            self.held.discard("left")
        elif event.key in RIGHT_KEYS:
            self.held.discard("right")

    def _on_blur(self, event: Any) -> None:
        """Losing focus drops key-up events: release keys and pause."""
        del event
        self.held.clear()
        if self.state == "playing":
            self._toggle_pause()

    def _on_resize(self, event: Any) -> None:
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
        requestAnimationFrame(self._frame_proxy)
