from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform

from snake_model import GameModel, Direction, PowerUpType
from game_widget import GameWidget
from highscore import load_high_score, save_high_score
import config

KEY_MAP = {
    273: Direction.UP,    119: Direction.UP,
    274: Direction.DOWN,  115: Direction.DOWN,
    276: Direction.LEFT,   97: Direction.LEFT,
    275: Direction.RIGHT, 100: Direction.RIGHT,
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
                'Swipe to move[/color]'
            ),
            font_size='15sp',
            markup=True,
            halign='center',
        ))

        layout.add_widget(Label(text='Select Difficulty', font_size='18sp'))

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

        self.model   = None
        self._kb     = None
        self._paused = False

        root = BoxLayout(orientation='vertical')

        # ── HUD ───────────────────────────────────────────────────────────────
        hud = BoxLayout(size_hint=(1, None), height=56, padding=(10, 4), spacing=8)

        self.score_label = Label(text='Score: 0', font_size='20sp',
                                 halign='left', size_hint=(0.35, 1))
        self.info_label  = Label(text='', font_size='15sp',
                                 halign='center', size_hint=(0.3, 1))

        self.pause_btn = Button(
            text='Pause',
            font_size='18sp',
            size_hint=(0.35, 1),
            background_color=(0.2, 0.2, 0.6, 1),
            background_normal='',
        )
        self.pause_btn.bind(on_press=self._toggle_pause)

        hud.add_widget(self.score_label)
        hud.add_widget(self.info_label)
        hud.add_widget(self.pause_btn)
        root.add_widget(hud)

        # ── Game canvas ───────────────────────────────────────────────────────
        self.game_widget = GameWidget()
        root.add_widget(self.game_widget)

        self.game_widget.bind(on_touch_down=self._touch_down)
        self.game_widget.bind(on_touch_up=self._touch_up)
        self._touch_start = None

        self.add_widget(root)

    # ── Screen lifecycle ──────────────────────────────────────────────────────

    def on_pre_enter(self, *_):
        self.model        = GameModel()
        self._paused      = False
        self.pause_btn.text = 'Pause'
        self.score_label.text = 'Score: 0'
        self.info_label.text  = ''

        # Only request keyboard on desktop — avoids popup on Android
        if platform not in ('android', 'ios'):
            self._kb = Window.request_keyboard(self._kb_closed, self)
            self._kb.bind(on_key_down=self._key_down)

        Clock.schedule_interval(self._tick, 1 / 60)

    def on_leave(self, *_):
        Clock.unschedule(self._tick)
        if self._kb:
            self._kb.unbind(on_key_down=self._key_down)
            self._kb.release()
            self._kb = None

    # ── Pause ─────────────────────────────────────────────────────────────────

    def _toggle_pause(self, *_):
        if self.model.state != 'running' and not self._paused:
            return
        self._paused = not self._paused
        self.pause_btn.text = 'Resume' if self._paused else 'Pause'

    # ── Game loop ─────────────────────────────────────────────────────────────

    def _tick(self, dt):
        if self._paused:
            return

        moved = self.model.tick(dt)

        if moved:
            self.game_widget.draw(self.model)
            self.score_label.text = f'Score: {self.model.score}'

            pu = self.model.powerup
            if pu:
                icon  = 'S+' if pu.kind == PowerUpType.SPEED else 'S-'
                label = 'Speed' if pu.kind == PowerUpType.SPEED else 'Shrink'
                self.info_label.text = f'{icon} {label} {pu.time_left:.1f}s'
            else:
                self.info_label.text = ''

        if self.model.state == 'dead':
            save_high_score(self.model.score)
            go_screen = self.manager.get_screen('gameover')
            go_screen.set_score(self.model.score)
            self.manager.current = 'gameover'

    # ── Keyboard ──────────────────────────────────────────────────────────────

    def _kb_closed(self):
        self._kb = None

    def _key_down(self, _kb, keycode, *_):
        direction = KEY_MAP.get(keycode[0])
        if direction:
            self.model.change_direction(direction)

    # ── Swipe ─────────────────────────────────────────────────────────────────

    def _touch_down(self, widget, touch):
        if widget.collide_point(*touch.pos):
            self._touch_start = touch.pos

    def _touch_up(self, widget, touch):
        if not self._touch_start:
            return
        sx, sy = self._touch_start
        dx     = touch.pos[0] - sx
        dy     = touch.pos[1] - sy

        if abs(dx) < 10 and abs(dy) < 10:
            return

        if abs(dx) > abs(dy):
            self.model.change_direction(Direction.RIGHT if dx > 0 else Direction.LEFT)
        else:
            self.model.change_direction(Direction.UP if dy > 0 else Direction.DOWN)

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
        self.score_label.text = f'Your Score: {score}'
        self.hs_label.text    = f'High Score: {load_high_score()}'
