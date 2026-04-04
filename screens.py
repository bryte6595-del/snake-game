from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
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

        layout = BoxLayout(orientation='vertical', padding=40, spacing=16)

        layout.add_widget(Label(
            text='SNAKE',
            font_size='56sp',
            bold=True,
            color=(0.25, 0.90, 0.25, 1),
        ))

        layout.add_widget(Label(
            text='[i][color=4488ff]By Bryte[/color][/i]',
            font_size='22sp',
            markup=True,
            halign='center',
        ))

        self.hs_label = Label(
            text=f'High Score: {load_high_score()}',
            font_size='22sp',
        )
        layout.add_widget(self.hs_label)

        layout.add_widget(Label(
            text=(
                '[color=aaaaaa]Eat the red food to grow.\n'
                'Blue = speed boost  |  Yellow = shrink tail\n'
                'Swipe to move[/color]'
            ),
            font_size='14sp',
            markup=True,
            halign='center',
        ))

        layout.add_widget(Label(text='Select Difficulty', font_size='18sp'))

        diff_row = BoxLayout(spacing=10, size_hint=(1, 0.18))
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
            diff_row.add_widget(btn)
        layout.add_widget(diff_row)

        self.selected_label = Label(
            text=f'Mode: {self._selected}',
            font_size='16sp',
            color=(0.80, 0.80, 0.80, 1),
        )
        layout.add_widget(self.selected_label)

        play_btn = Button(text='Play', font_size='30sp', size_hint=(1, 0.22))
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

        # FloatLayout lets us overlay the Game Over panel on the grid
        root = FloatLayout()

        # ── Main game layout (fills screen) ───────────────────────────────────
        game_layout = BoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0},
        )

        # ── Top bar: pause button only ────────────────────────────────────────
        top_bar = BoxLayout(size_hint=(1, None), height=52, padding=(8, 4))

        self.info_label = Label(
            text='',
            font_size='15sp',
            halign='left',
            size_hint=(0.7, 1),
        )
        self.pause_btn = Button(
            text='II',
            font_size='22sp',
            bold=True,
            size_hint=(0.3, 1),
            background_color=(0.15, 0.15, 0.50, 1),
            background_normal='',
        )
        self.pause_btn.bind(on_press=self._toggle_pause)
        top_bar.add_widget(self.info_label)
        top_bar.add_widget(self.pause_btn)
        game_layout.add_widget(top_bar)

        # ── Game canvas ───────────────────────────────────────────────────────
        self.game_widget = GameWidget()
        game_layout.add_widget(self.game_widget)

        # ── Bottom bar: score and high score ──────────────────────────────────
        bottom_bar = BoxLayout(size_hint=(1, None), height=48, padding=(10, 4))

        self.score_label = Label(
            text='Score: 0',
            font_size='20sp',
            halign='left',
            size_hint=(0.5, 1),
        )
        self.hs_label = Label(
            text=f'Best: {load_high_score()}',
            font_size='20sp',
            halign='right',
            size_hint=(0.5, 1),
        )
        bottom_bar.add_widget(self.score_label)
        bottom_bar.add_widget(self.hs_label)
        game_layout.add_widget(bottom_bar)

        root.add_widget(game_layout)

        # ── Game Over overlay (hidden initially) ──────────────────────────────
        self.overlay = BoxLayout(
            orientation='vertical',
            padding=30,
            spacing=14,
            size_hint=(0.85, 0.55),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
        )
        from kivy.graphics import Color, RoundedRectangle
        with self.overlay.canvas.before:
            Color(0.05, 0.05, 0.05, 0.93)
            self._overlay_bg = RoundedRectangle(
                pos=self.overlay.pos,
                size=self.overlay.size,
                radius=[16],
            )
        self.overlay.bind(
            pos=lambda w, v: setattr(self._overlay_bg, 'pos', v),
            size=lambda w, v: setattr(self._overlay_bg, 'size', v),
        )

        self.overlay.add_widget(Label(
            text='Game Over',
            font_size='36sp',
            bold=True,
            color=(0.95, 0.25, 0.25, 1),
        ))
        self.over_score_label = Label(text='', font_size='24sp')
        self.over_hs_label    = Label(text='', font_size='18sp',
                                      color=(0.95, 0.85, 0.15, 1))
        self.overlay.add_widget(self.over_score_label)
        self.overlay.add_widget(self.over_hs_label)

        btn_row = BoxLayout(spacing=12, size_hint=(1, None), height=52)
        retry_btn = Button(text='Play Again', font_size='20sp')
        menu_btn  = Button(text='Menu',       font_size='20sp')
        retry_btn.bind(on_press=self._retry)
        menu_btn.bind( on_press=lambda *_: setattr(self.manager, 'current', 'menu'))
        btn_row.add_widget(retry_btn)
        btn_row.add_widget(menu_btn)
        self.overlay.add_widget(btn_row)

        self.overlay.opacity = 0  # hidden at start
        root.add_widget(self.overlay)

        # Swipe tracking
        self.game_widget.bind(on_touch_down=self._touch_down)
        self.game_widget.bind(on_touch_up=self._touch_up)
        self._touch_start = None

        self.add_widget(root)

    # ── Screen lifecycle ──────────────────────────────────────────────────────

    def on_pre_enter(self, *_):
        self.model              = GameModel()
        self._paused            = False
        self.overlay.opacity    = 0
        self.pause_btn.text     = 'II'
        self.score_label.text   = 'Score: 0'
        self.hs_label.text      = f'Best: {load_high_score()}'
        self.info_label.text    = ''

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
        self.pause_btn.text = '▶' if self._paused else 'II'

    def _retry(self, *_):
        self.overlay.opacity = 0
        self.on_pre_enter()

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
                label = 'Speed' if pu.kind == PowerUpType.SPEED else 'Shrink'
                self.info_label.text = f'{label} {pu.time_left:.1f}s'
            else:
                self.info_label.text = ''

        if self.model.state == 'dead':
            save_high_score(self.model.score)
            self.over_score_label.text = f'Your Score: {self.model.score}'
            self.over_hs_label.text    = f'High Score: {load_high_score()}'
            self.overlay.opacity       = 1

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
