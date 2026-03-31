"""
screens.py — The three screens of the game.

Flow:  MenuScreen → GameScreen → GameOverScreen → (back to either)

MenuScreen    : shows the high score and a Play button
GameScreen    : runs the game loop; handles keyboard + swipe input
GameOverScreen: shows the final score and lets the player retry or go to menu
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.window import Window

import config
from snake_model import GameModel, Direction, PowerUpType
from game_widget import GameWidget
from highscore import load_high_score, save_high_score


# ── Keyboard → Direction mapping ─────────────────────────────────────────────
# Supports arrow keys and WASD
KEY_MAP = {
    273: Direction.UP,    119: Direction.UP,    # ↑  W
    274: Direction.DOWN,  115: Direction.DOWN,  # ↓  S
    276: Direction.LEFT,   97: Direction.LEFT,  # ←  A
    275: Direction.RIGHT, 100: Direction.RIGHT, # →  D
}


# ── Menu Screen ───────────────────────────────────────────────────────────────

class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._selected = config.DEFAULT_DIFFICULTY
        self._diff_buttons = {}

        layout = BoxLayout(orientation='vertical', padding=40, spacing=16)

        layout.add_widget(Label(
            text='SNAKE',
            font_size='52sp',
            bold=True,
            color=(0.25, 0.90, 0.25, 1),
        ))

        self.hs_label = Label(
            text=f'High Score: {load_high_score()}',
            font_size='24sp',
        )
        layout.add_widget(self.hs_label)

        layout.add_widget(Label(
            text=(
                '[color=aaaaaa]Eat the red food to grow.\n'
                'Blue = speed boost  |  Yellow = shrink tail\n'
                'Arrow keys / WASD to move[/color]'
            ),
            font_size='15sp',
            markup=True,
            halign='center',
        ))

        # ── Difficulty label ──────────────────────────────────────────────────
        layout.add_widget(Label(text='Select Difficulty', font_size='18sp'))

        # ── Difficulty buttons row ────────────────────────────────────────────
        diff_row = BoxLayout(spacing=10, size_hint=(1, 0.2))
        colours = {
            'Easy':   (0.10, 0.75, 0.10, 1),
            'Normal': (0.90, 0.75, 0.10, 1),
            'Hard':   (0.85, 0.15, 0.15, 1),
        }
        for level in ['Easy', 'Normal', 'Hard']:
            btn = Button(
                text=level,
                font_size='20sp',
                background_color=colours[level],
                background_normal='',
            )
            btn.bind(on_press=lambda b, l=level: self._pick_difficulty(l))
            self._diff_buttons[level] = btn
            diff_row.add_widget(btn)
        layout.add_widget(diff_row)

        # Show which is currently selected
        self.selected_label = Label(
            text=f'Mode: {self._selected}',
            font_size='16sp',
            color=(0.80, 0.80, 0.80, 1),
        )
        layout.add_widget(self.selected_label)

        play_btn = Button(text='Play', font_size='30sp', size_hint=(1, 0.25))
        play_btn.bind(on_press=self._start_game)
        layout.add_widget(play_btn)

        self.add_widget(layout)

    def _pick_difficulty(self, level):
        self._selected = level
        self.selected_label.text = f'Mode: {level}'

    def _start_game(self, *_):
        # Apply difficulty settings to config before GameScreen reads them
        interval, min_iv, step = config.DIFFICULTY[self._selected]
        config.INITIAL_INTERVAL = interval
        config.MIN_INTERVAL     = min_iv
        config.SPEED_STEP       = step
        self.manager.current    = 'game'

    def on_pre_enter(self, *_):
        self.hs_label.text = f'High Score: {load_high_score()}'


# ── Game Screen ───────────────────────────────────────────────────────────────

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.model = None
        self._kb   = None

        root = BoxLayout(orientation='vertical')

        # ── HUD bar at the top ────────────────────────────────────────────────
        hud = BoxLayout(size_hint=(1, None), height=48, padding=(10, 4))

        self.score_label = Label(text='Score: 0', font_size='20sp', halign='left',
                                 text_size=(200, None))
        self.info_label  = Label(text='',         font_size='16sp', halign='center')
        self.hs_label    = Label(text='Best: 0',  font_size='20sp', halign='right',
                                 text_size=(200, None))

        hud.add_widget(self.score_label)
        hud.add_widget(self.info_label)
        hud.add_widget(self.hs_label)
        root.add_widget(hud)

        # ── Game canvas ───────────────────────────────────────────────────────
        self.game_widget = GameWidget()
        root.add_widget(self.game_widget)

        # Swipe gesture tracking
        self.game_widget.bind(on_touch_down=self._touch_down)
        self.game_widget.bind(on_touch_up=self._touch_up)
        self._touch_start = None

        self.add_widget(root)

    # ── Screen lifecycle ──────────────────────────────────────────────────────

    def on_pre_enter(self, *_):
        """Called each time we navigate to this screen — starts a fresh game."""
        self.model           = GameModel()
        self.hs_label.text   = f'Best: {load_high_score()}'
        self.score_label.text = 'Score: 0'
        self.info_label.text  = ''

        # Keyboard
        self._kb = Window.request_keyboard(self._kb_closed, self)
        self._kb.bind(on_key_down=self._key_down)

        # Game loop: 60 fps clock tick
        Clock.schedule_interval(self._tick, 1 / 60)

    def on_leave(self, *_):
        """Clean up when leaving so we don't double-tick on the next game."""
        Clock.unschedule(self._tick)
        if self._kb:
            self._kb.unbind(on_key_down=self._key_down)
            self._kb.release()
            self._kb = None

    # ── Game loop ─────────────────────────────────────────────────────────────

    def _tick(self, dt):
        moved = self.model.tick(dt)

        if moved:
            # Redraw only when the snake actually stepped
            self.game_widget.draw(self.model)
            self.score_label.text = f'Score: {self.model.score}'

            # Update power-up info label
            pu = self.model.powerup
            if pu:
                icon = '⚡' if pu.kind == PowerUpType.SPEED else '✂'
                label = 'Speed' if pu.kind == PowerUpType.SPEED else 'Shrink'
                self.info_label.text = f'{icon} {label}! {pu.time_left:.1f}s'
            else:
                self.info_label.text = ''

        # Check for game over
        if self.model.state == 'dead':
            save_high_score(self.model.score)
            go_screen = self.manager.get_screen('gameover')
            go_screen.set_score(self.model.score)
            self.manager.current = 'gameover'

    # ── Keyboard input ────────────────────────────────────────────────────────

    def _kb_closed(self):
        self._kb = None

    def _key_down(self, _kb, keycode, *_):
        direction = KEY_MAP.get(keycode[0])
        if direction:
            self.model.change_direction(direction)

    # ── Touch / swipe input (for mobile) ─────────────────────────────────────

    def _touch_down(self, widget, touch):
        if widget.collide_point(*touch.pos):
            self._touch_start = touch.pos

    def _touch_up(self, widget, touch):
        if not self._touch_start:
            return

        sx, sy = self._touch_start
        dx     = touch.pos[0] - sx
        dy     = touch.pos[1] - sy

        # Ignore taps (too small to be a swipe)
        if abs(dx) < 10 and abs(dy) < 10:
            return

        if abs(dx) > abs(dy):
            self.model.change_direction(Direction.RIGHT if dx > 0 else Direction.LEFT)
        else:
            self.model.change_direction(Direction.UP    if dy > 0 else Direction.DOWN)

        self._touch_start = None


# ── Game Over Screen ──────────────────────────────────────────────────────────

class GameOverScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation='vertical', padding=40, spacing=16)

        layout.add_widget(Label(
            text='Game Over',
            font_size='44sp',
            bold=True,
            color=(0.95, 0.25, 0.25, 1),
        ))

        self.score_label = Label(text='', font_size='28sp')
        self.hs_label    = Label(text='', font_size='20sp',
                                 color=(0.95, 0.85, 0.15, 1))
        layout.add_widget(self.score_label)
        layout.add_widget(self.hs_label)

        btn_row = BoxLayout(spacing=16, size_hint=(1, 0.25))

        retry_btn = Button(text='Play Again', font_size='24sp')
        menu_btn  = Button(text='Menu',       font_size='24sp')

        retry_btn.bind(on_press=lambda *_: setattr(self.manager, 'current', 'game'))
        menu_btn.bind( on_press=lambda *_: setattr(self.manager, 'current', 'menu'))

        btn_row.add_widget(retry_btn)
        btn_row.add_widget(menu_btn)
        layout.add_widget(btn_row)

        self.add_widget(layout)

    def set_score(self, score: int):
        """Called by GameScreen before navigating here."""
        self.score_label.text = f'Your Score: {score}'
        self.hs_label.text    = f'High Score: {load_high_score()}'
