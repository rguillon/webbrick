"""Layout, tuning and input constants (all sizes in logical px)."""

from __future__ import annotations

import math

WIDTH = 480
HEIGHT = 600
HUD_H = 40

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
BRICK_W = 41
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
MAX_PARTICLES = 300
STAGE_INSET = 2  # px kept free around the canvas for its CSS outline

STORAGE_KEY = "brickbreaker.cleared"

LEFT_KEYS = frozenset(("ArrowLeft", "a", "A"))
RIGHT_KEYS = frozenset(("ArrowRight", "d", "D"))
CONFIRM_KEYS = frozenset(("Enter", " "))
SCROLL_KEYS = frozenset(("ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", " "))

# Level-select menu geometry (2 columns of cards)
CARD_COLS = 2
CARD_W = 200
CARD_H = 128
CARD_GAP_X = 20
CARD_GAP_Y = 16
CARD_LEFT = (WIDTH - CARD_COLS * CARD_W - (CARD_COLS - 1) * CARD_GAP_X) // 2
CARD_TOP = 150
PREVIEW_CELL_W = 14
PREVIEW_CELL_H = 6
PREVIEW_GAP = 2
