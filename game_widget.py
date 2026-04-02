from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse

from config import (
    GRID_COLS, GRID_ROWS,
    C_BACKGROUND, C_GRID_LINE,
    C_SNAKE_HEAD, C_SNAKE_BODY,
    C_FOOD, C_PU_SPEED, C_PU_SHRINK,
)
from snake_model import PowerUpType


class GameWidget(Widget):

    def draw(self, model):
        self.canvas.clear()

        # Force square cells
        cell   = min(self.width / GRID_COLS, self.height / GRID_ROWS)
        grid_w = cell * GRID_COLS
        grid_h = cell * GRID_ROWS

        # Centre the grid
        ox = self.x + (self.width  - grid_w) / 2
        oy = self.y + (self.height - grid_h) / 2

        with self.canvas:

            # Background
            Color(*C_BACKGROUND)
            Rectangle(pos=self.pos, size=self.size)

            # Grid area
            Color(0.08, 0.08, 0.08, 1)
            Rectangle(pos=(ox, oy), size=(grid_w, grid_h))

            # Grid lines
            Color(*C_GRID_LINE)
            for col in range(GRID_COLS + 1):
                Rectangle(pos=(ox + col * cell, oy), size=(1, grid_h))
            for row in range(GRID_ROWS + 1):
                Rectangle(pos=(ox, oy + row * cell), size=(grid_w, 1))

            # Food - circle
            fx, fy = model.food.position
            pad = cell * 0.15
            Color(*C_FOOD)
            Ellipse(
                pos=(ox + fx * cell + pad, oy + fy * cell + pad),
                size=(cell - pad * 2, cell - pad * 2),
            )

            # Power-up - circle
            if model.powerup:
                px, py = model.powerup.position
                pu_color = C_PU_SPEED if model.powerup.kind == PowerUpType.SPEED else C_PU_SHRINK
                Color(*pu_color)
                Ellipse(
                    pos=(ox + px * cell + pad, oy + py * cell + pad),
                    size=(cell - pad * 2, cell - pad * 2),
                )

            # Snake - rounded rectangles
            length = len(model.snake.body)
            radius = max(2, cell * 0.25)
            for i, (bx, by) in enumerate(reversed(model.snake.body)):
                is_head = (i == length - 1)
                Color(*(C_SNAKE_HEAD if is_head else C_SNAKE_BODY))
                RoundedRectangle(
                    pos=(ox + bx * cell + 1, oy + by * cell + 1),
                    size=(cell - 2, cell - 2),
                    radius=[radius],
                )
