"""
Клавиатуры для ClubBot.
"""

from .main import get_main_keyboard, get_payment_keyboard, get_reports_keyboard
from .rituals import get_ritual_keyboard, get_ritual_response_keyboard
from .goals import get_goals_keyboard, get_goal_actions_keyboard
from .admin import get_admin_keyboard

__all__ = [
    "get_main_keyboard",
    "get_payment_keyboard",
    "get_reports_keyboard",
    "get_ritual_keyboard",
    "get_ritual_response_keyboard",
    "get_goals_keyboard",
    "get_goal_actions_keyboard",
    "get_admin_keyboard"
]
