"""
game_widget.py — The Kivy widget that draws the game grid.

It knows nothing about game rules; it just reads the GameModel and paints.
Call draw(model) once after every move.
"""

from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle

from config import (
    GRID_COLS, GRID_ROWS,
    C_BACKGROUND, C_GRID_LINE,
    C_SNAKE_HEAD, C_SNAKE_BODY,
    C_FOOD, C_PU_SPEED, C_PU_SHRINK,
)
from snake_model import PowerUpType


class GameWidget(Widget):

    def draw(self, model):
        """Clear and repaint the entire grid from the current model state."""
        self.canvas.clear()

        # Cell size in pixels (adapts to whatever screen size Kivy gives us)
        cw = self.width  / GRID_COLS
        ch = self.height / GRID_ROWS

        with self.canvas:

            # ── Background ────────────────────────────────────────────────────
            Color(*C_BACKGROUND)
            Rectangle(pos=self.pos, size=self.size)

            # ── Subtle grid lines ─────────────────────────────────────────────
            Color(*C_GRID_LINE)
            for col in range(GRID_COLS + 1):
                Rectangle(
                    pos=(self.x + col * cw, self.y),
                    size=(1, self.height),
                )
            for row in range(GRID_ROWS + 1):
                Rectangle(
                    pos=(self.x, self.y + row * ch),
                    size=(self.width, 1),
                )

            # ── Food ──────────────────────────────────────────────────────────
            fx, fy = model.food.position
            Color(*C_FOOD)
            Rectangle(
                pos=(self.x + fx * cw + 2, self.y + fy * ch + 2),
                size=(cw - 4, ch - 4),
            )

            # ── Power-up (if one is on the grid) ──────────────────────────────
            if model.powerup:
                px, py = model.powerup.position
                pu_color = (
                    C_PU_SPEED
                    if model.powerup.kind == PowerUpType.SPEED
                    else C_PU_SHRINK
                )
                Color(*pu_color)
                Rectangle(
                    pos=(self.x + px * cw + 2, self.y + py * ch + 2),
                    size=(cw - 4, ch - 4),
                )

            # ── Snake (draw tail → body → head so head is on top) ─────────────
            length = len(model.snake.body)
            for i, (bx, by) in enumerate(reversed(model.snake.body)):
                # i == length-1 means we've reached the head (index 0 of body)
                is_head = (i == length - 1)
                Color(*(C_SNAKE_HEAD if is_head else C_SNAKE_BODY))
                Rectangle(
                    pos=(self.x + bx * cw + 1, self.y + by * ch + 1),
                    size=(cw - 2, ch - 2),
                )
