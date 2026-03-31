"""
highscore.py — Saves and loads the all-time high score to / from disk.

We use a simple JSON file so it survives between app sessions.
"""

import json
import os
from config import HIGH_SCORE_FILE


def load_high_score() -> int:
    """Return the stored high score, or 0 if no file exists yet."""
    if not os.path.exists(HIGH_SCORE_FILE):
        return 0
    try:
        with open(HIGH_SCORE_FILE, "r") as f:
            data = json.load(f)
            return int(data.get("high_score", 0))
    except (json.JSONDecodeError, ValueError):
        return 0  # corrupted file — just start fresh


def save_high_score(score: int) -> None:
    """Overwrite the file only when the new score beats the old one."""
    current = load_high_score()
    if score > current:
        with open(HIGH_SCORE_FILE, "w") as f:
            json.dump({"high_score": score}, f)
