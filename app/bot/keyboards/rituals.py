"""
Клавиатуры для ритуалов ClubBot.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_ritual_keyboard(ritual_id: str) -> InlineKeyboardMarkup:
    """Получить клавиатуру для ритуала."""
    keyboard = [
        [InlineKeyboardButton("✅ Начать ритуал", callback_data=f"ritual_start_{ritual_id}")],
        [InlineKeyboardButton("⏭️ Пропустить", callback_data=f"ritual_skip_{ritual_id}")],
        [InlineKeyboardButton("📊 Статистика ритуалов", callback_data="ritual_stats")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_ritual_response_keyboard(ritual_id: str) -> InlineKeyboardMarkup:
    """Получить клавиатуру для ответа на ритуал."""
    keyboard = [
        [InlineKeyboardButton("✅ Завершить ритуал", callback_data=f"ritual_complete_{ritual_id}")],
        [InlineKeyboardButton("❌ Отменить", callback_data=f"ritual_cancel_{ritual_id}")],
        [InlineKeyboardButton("⏭️ Пропустить", callback_data=f"ritual_skip_{ritual_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_rituals_list_keyboard() -> InlineKeyboardMarkup:
    """Получить клавиатуру списка ритуалов."""
    keyboard = [
        [InlineKeyboardButton("🌅 Утренние ритуалы", callback_data="ritual_morning")],
        [InlineKeyboardButton("🌙 Вечерние ритуалы", callback_data="ritual_evening")],
        [InlineKeyboardButton("📊 Статистика ритуалов", callback_data="ritual_stats")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_ritual_stats_keyboard() -> InlineKeyboardMarkup:
    """Получить клавиатуру статистики ритуалов."""
    keyboard = [
        [InlineKeyboardButton("📊 Общая статистика", callback_data="ritual_stats_general")],
        [InlineKeyboardButton("🌅 Утренние ритуалы", callback_data="ritual_stats_morning")],
        [InlineKeyboardButton("🌙 Вечерние ритуалы", callback_data="ritual_stats_evening")],
        [InlineKeyboardButton("📈 Прогресс", callback_data="ritual_stats_progress")],
        [InlineKeyboardButton("🔙 Назад", callback_data="rituals_list")]
    ]
    return InlineKeyboardMarkup(keyboard)
