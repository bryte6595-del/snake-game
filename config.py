"""
config.py — All game constants live here.
Tweak these values to change the feel of the game without touching any logic.
"""

# ── Grid ──────────────────────────────────────────────────────────────────────
GRID_COLS = 20   # number of columns
GRID_ROWS = 20   # number of rows

# ── Difficulty levels ─────────────────────────────────────────────────────────
# Each tuple is (INITIAL_INTERVAL, MIN_INTERVAL, SPEED_STEP)
# INITIAL_INTERVAL → starting speed (higher = slower start)
# MIN_INTERVAL     → fastest the snake can ever get
# SPEED_STEP       → how much faster it gets per food eaten
DIFFICULTY = {
    "Easy":   (0.25, 0.12, 0.003),
    "Normal": (0.15, 0.06, 0.005),
    "Hard":   (0.08, 0.03, 0.008),
}
DEFAULT_DIFFICULTY = "Normal"

# These get overwritten at runtime when the player picks a difficulty
INITIAL_INTERVAL = 0.15
MIN_INTERVAL     = 0.06
SPEED_STEP       = 0.005

# ── Power-ups ─────────────────────────────────────────────────────────────────
POWERUP_CHANCE   = 0.20   # 20 % chance a power-up spawns after eating food
POWERUP_DURATION = 6.0    # seconds before a power-up disappears

# ── File used to remember the high score between sessions ────────────────────
HIGH_SCORE_FILE = "highscore.json"

# ── Colours  (Kivy RGBA — each value is 0.0 to 1.0) ─────────────────────────
C_BACKGROUND  = (0.05, 0.05, 0.05, 1)
C_GRID_LINE   = (0.13, 0.13, 0.13, 1)
C_SNAKE_HEAD  = (0.25, 0.90, 0.25, 1)   # bright green
C_SNAKE_BODY  = (0.10, 0.65, 0.10, 1)   # darker green
C_FOOD        = (0.95, 0.25, 0.25, 1)   # red
C_PU_SPEED    = (0.25, 0.55, 0.95, 1)   # blue  → speed boost power-up
C_PU_SHRINK   = (0.95, 0.85, 0.15, 1)   # yellow→ shrink power-up
