"""
snake_model.py — Pure-Python game logic.  Zero Kivy here.

Classes
-------
Direction   : simple direction constants (no enum needed)
PowerUpType : what kind of bonus a power-up gives
Snake       : the snake's body, movement, and growth
Food        : the red pellet the snake eats
PowerUp     : a temporary bonus item that appears on the grid
GameModel   : orchestrates everything; call tick(dt) every frame
"""

import random
from enum import Enum

import config
from config import (
    GRID_COLS, GRID_ROWS,
    POWERUP_CHANCE, POWERUP_DURATION,
)


# ── Direction constants ───────────────────────────────────────────────────────

class Direction:
    UP    = ( 0,  1)
    DOWN  = ( 0, -1)
    LEFT  = (-1,  0)
    RIGHT = ( 1,  0)

    # Map each direction to the one it cannot reverse into
    OPPOSITES = {
        UP: DOWN, DOWN: UP,
        LEFT: RIGHT, RIGHT: LEFT,
    }


# ── Power-up types ────────────────────────────────────────────────────────────

class PowerUpType(Enum):
    SPEED  = "speed"   # snake moves 40 % faster for a few seconds
    SHRINK = "shrink"  # snake's tail is cut in half instantly


# ── Snake ─────────────────────────────────────────────────────────────────────

class Snake:
    def __init__(self):
        # Start in the centre of the grid, heading right, length 3
        cx, cy = GRID_COLS // 2, GRID_ROWS // 2
        self.body      = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]  # head is [0]
        self.direction = Direction.RIGHT
        self.grow_pending = 0  # extra tail segments to add on next moves

    @property
    def head(self):
        return self.body[0]

    def change_direction(self, new_dir):
        """Refuse 180-degree U-turns; everything else is fine."""
        if new_dir != Direction.OPPOSITES.get(self.direction):
            self.direction = new_dir

    def move(self):
        """
        Add a new head one step in the current direction.
        Only remove the tail if we're not growing.
        """
        hx, hy    = self.head
        dx, dy    = self.direction
        new_head  = (hx + dx, hy + dy)
        self.body.insert(0, new_head)

        if self.grow_pending > 0:
            self.grow_pending -= 1   # keep the tail — snake gets longer
        else:
            self.body.pop()          # remove the tail — length stays the same

    def grow(self, amount: int = 1):
        """Queue extra tail segments."""
        self.grow_pending += amount

    def shrink(self):
        """Cut the tail in half (but keep at least 3 segments)."""
        target    = max(3, len(self.body) // 2)
        self.body = self.body[:target]

    def collides_with_self(self) -> bool:
        return self.head in self.body[1:]

    def out_of_bounds(self) -> bool:
        x, y = self.head
        return not (0 <= x < GRID_COLS and 0 <= y < GRID_ROWS)


# ── Food ──────────────────────────────────────────────────────────────────────

class Food:
    def __init__(self, occupied: set):
        self.position = self._random_free_cell(occupied)

    @staticmethod
    def _random_free_cell(occupied: set):
        free = [
            (x, y)
            for x in range(GRID_COLS)
            for y in range(GRID_ROWS)
            if (x, y) not in occupied
        ]
        return random.choice(free) if free else (0, 0)


# ── PowerUp ───────────────────────────────────────────────────────────────────

class PowerUp:
    def __init__(self, kind: PowerUpType, occupied: set):
        self.kind      = kind
        self.position  = Food._random_free_cell(occupied)
        self.time_left = POWERUP_DURATION  # counts down each tick

    def tick(self, dt: float) -> bool:
        """Reduce timer. Returns False when the power-up has expired."""
        self.time_left -= dt
        return self.time_left > 0


# ── GameModel ─────────────────────────────────────────────────────────────────

class GameModel:
    """
    One complete game session.

    Usage
    -----
    model = GameModel()
    # each frame:
    moved = model.tick(dt)
    if moved:
        redraw()          # only redraw when the snake actually stepped
    if model.state == 'dead':
        show_game_over()
    """

    def __init__(self):
        self.snake    = Snake()
        self.score    = 0
        self.interval = config.INITIAL_INTERVAL   # seconds per move step
        self.state    = "running"          # 'running' | 'dead'

        occupied      = set(self.snake.body)
        self.food     = Food(occupied)
        self.powerup  = None               # PowerUp instance or None

        self._speed_boost = False          # True while a SPEED power-up is active
        self._elapsed     = 0.0           # time accumulated since last move

    # ── Public interface ──────────────────────────────────────────────────────

    def change_direction(self, direction):
        if self.state == "running":
            self.snake.change_direction(direction)

    def tick(self, dt: float) -> bool:
        """
        Advance the game by dt seconds.
        Returns True only when the snake physically moved — use this as the
        signal to redraw.
        """
        if self.state != "running":
            return False

        # Count down any active power-up
        if self.powerup and not self.powerup.tick(dt):
            self._expire_powerup()

        self._elapsed += dt

        # Apply speed-boost: snake effectively moves 40 % faster
        effective_interval = self.interval * (0.6 if self._speed_boost else 1.0)

        if self._elapsed < effective_interval:
            return False   # not time to move yet

        self._elapsed = 0.0
        self._step()
        return True

    # ── Private ───────────────────────────────────────────────────────────────

    def _step(self):
        """Execute one snake move and handle all collisions / pickups."""
        self.snake.move()

        # Wall or self collision → game over
        if self.snake.out_of_bounds() or self.snake.collides_with_self():
            self.state = "dead"
            return

        head = self.snake.head

        # Eat food?
        if head == self.food.position:
            self.snake.grow()
            self.score += 10
            self._increase_difficulty()
            self._maybe_spawn_powerup()
            # Spawn new food away from snake and any existing power-up
            occupied = set(self.snake.body) | (
                {self.powerup.position} if self.powerup else set()
            )
            self.food = Food(occupied)

        # Collect power-up?
        if self.powerup and head == self.powerup.position:
            self._apply_powerup()

    def _increase_difficulty(self):
        """Each food eaten makes the snake a tiny bit faster."""
        self.interval = max(config.MIN_INTERVAL, self.interval - config.SPEED_STEP)

    def _maybe_spawn_powerup(self):
        """Randomly spawn a power-up after eating food (only one at a time)."""
        if self.powerup:
            return
        if random.random() < POWERUP_CHANCE:
            kind     = random.choice(list(PowerUpType))
            occupied = set(self.snake.body) | {self.food.position}
            self.powerup = PowerUp(kind, occupied)

    def _apply_powerup(self):
        if self.powerup.kind == PowerUpType.SPEED:
            self._speed_boost = True
            # power-up stays visible but counts down — effect ends when it expires
            # We leave self.powerup alive so the timer still ticks
        elif self.powerup.kind == PowerUpType.SHRINK:
            self.snake.shrink()
            self.powerup = None   # shrink is instant — remove immediately

    def _expire_powerup(self):
        """Called when the power-up timer runs out."""
        if self.powerup and self.powerup.kind == PowerUpType.SPEED:
            self._speed_boost = False
        self.powerup = None
