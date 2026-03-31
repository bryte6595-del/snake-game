"""
main.py — Entry point.

Run with:
    python main.py
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager

from screens import MenuScreen, GameScreen, GameOverScreen


class SnakeApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(GameScreen(name='game'))
        sm.add_widget(GameOverScreen(name='gameover'))
        return sm


if __name__ == '__main__':
    SnakeApp().run()
