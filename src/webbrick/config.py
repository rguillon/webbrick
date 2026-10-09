"""Layout, tuning and input constants (all sizes in logical px)."""

from __future__ import annotations

import math

WIDTH = 480
HEIGHT = 600
HUD_H = 40
PIXEL = 2  # logical px per pixel-art pixel: sprites are drawn on this grid

PADDLE_W = 90
PADDLE_H = 14
PADDLE_Y = HEIGHT - 46
PADDLE_SPEED = 480.0  # px/s

BALL_R = 7
BALL_SPEED = 280.0  # px/s on level 1
BALL_SPEED_STEP = 20.0  # extra px/s per level
MAX_BALL_STEP = 4.0  # sub-step size so the ball can't tunnel through bricks
MAX_TILT = math.radians(55)  # steepest paddle-bounce angle from vertical
TRAIL_LEN = 8

BRICK_COLS = 10
BRICK_W = 40
BRICK_H = 18
BRICK_GAP = 4
BRICK_TOP = HUD_H + 40
SIDE_MARGIN = (WIDTH - BRICK_COLS * BRICK_W - (BRICK_COLS - 1) * BRICK_GAP) // 2
ROW_COLORS = (
    "#ef4444",
    "#f97316",
    "#eab308",
    "#22c55e",
    "#14b8a6",
    "#3b82f6",
    "#8b5cf6",
    "#ec4899",
)
STEEL = "#64748b"
FLASH_TIME = 0.12

POINTS_PER_HIT = 10
LEVEL_BONUS = 100  # times the level number
LIVES_START = 3

# Sparks thrown when bricks break, capsules are caught and lives are lost.
MAX_PARTICLES = 300
PARTICLE_SPEED = (60.0, 220.0)  # spawn speed range, px/s
PARTICLE_LIFE = (0.4, 0.9)  # spawn lifetime range, s
PARTICLE_SIZE = (2.0, 4.0)  # spawn size range, drawn as one or two art px
PARTICLE_GRAVITY = 420.0  # px/s² pulling the sparks down

# Bonus bricks drop a capsule that falls slowly; touch it with the paddle to win it.
BONUS_CHANCE = 0.15  # share of breakable bricks that carry a bonus
POWERUP_W = 34
POWERUP_H = 16
POWERUP_FALL_SPEED = 90.0  # px/s
# kind: (capsule label, color, drop weight)
POWERUPS = {
    "multi": ("\N{MULTIPLICATION SIGN}3", "#a855f7", 3),  # two extra balls
    "pierce": ("FIRE", "#f97316", 2),  # ball runs through bricks
    "life": ("♥", "#ef4444", 1),  # extra life
    "speed": ("FAST", "#eab308", 3),  # faster ball
    "gun": ("GUN", "#84cc16", 2),  # paddle shoots bullets
}
PIERCE_TIME = 10.0  # s
SPEED_TIME = 10.0  # s
GUN_TIME = 5.0  # s
BULLET_W = 4
BULLET_H = 10
BULLET_SPEED = 620.0  # px/s
BULLET_INTERVAL = 0.2  # s between volleys while the fire key is held
SPEED_BOOST = 1.35  # ball speed multiplier while "speed" is active
MULTI_SPREAD = math.radians(25)  # angle between the split balls
MAX_LIVES = 6
LIFE_POINTS = 100  # awarded instead of a life when lives are full
TEXT_CACHE_SIZE = 128  # rendered strings kept before the cache is emptied
STAGE_INSET = 2  # px kept free around the canvas for its CSS outline

STORAGE_KEY = "brickbreaker.cleared"

LEFT_KEYS = frozenset(("ArrowLeft", "a", "A"))
RIGHT_KEYS = frozenset(("ArrowRight", "d", "D"))
CONFIRM_KEYS = frozenset(("Enter", " "))
SCROLL_KEYS = frozenset(("ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", " "))

# Level-select menu geometry (2 columns of cards)
CARD_COLS = 2
CARD_ROWS = 3
CARDS_PER_PAGE = CARD_COLS * CARD_ROWS  # the menu shows one page of cards at a time
CARD_W = 200
CARD_H = 128
CARD_GAP_X = 20
CARD_GAP_Y = 16
CARD_LEFT = (WIDTH - CARD_COLS * CARD_W - (CARD_COLS - 1) * CARD_GAP_X) // 2
CARD_TOP = 150
PREVIEW_CELL_W = 14
PREVIEW_CELL_H = 6
PREVIEW_GAP = 2
