"""
Клавиатуры для работы с целями.

Содержит функции для создания inline клавиатур для управления целями пользователей.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_goals_keyboard() -> InlineKeyboardMarkup:
    """
    Создание клавиатуры для работы с целями.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура целей
    """
    keyboard = [
        [InlineKeyboardButton("🎯 Мои цели", callback_data="my_goals")],
        [InlineKeyboardButton("➕ Новая цель", callback_data="create_goal")],
        [InlineKeyboardButton("📊 Статистика", callback_data="goals_stats")],
        [InlineKeyboardButton("✅ Выполненные", callback_data="goals_completed")],
        [InlineKeyboardButton("← Главное меню", callback_data="main_menu")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_goal_actions_keyboard(goal_id: str) -> InlineKeyboardMarkup:
    """
    Создание клавиатуры действий с конкретной целью.
    
    Args:
        goal_id: ID цели
        
    Returns:
        InlineKeyboardMarkup: Клавиатура действий с целью
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Выполнить", callback_data=f"goal_complete_{goal_id}"),
            InlineKeyboardButton("✏️ Редактировать", callback_data=f"goal_edit_{goal_id}")
        ],
        [
            InlineKeyboardButton("⏰ Отложить", callback_data=f"goal_postpone_{goal_id}"),
            InlineKeyboardButton("❌ Удалить", callback_data=f"goal_delete_{goal_id}")
        ],
        [InlineKeyboardButton("← Назад к целям", callback_data="my_goals")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_goal_creation_keyboard() -> InlineKeyboardMarkup:
    """
    Создание клавиатуры для создания новой цели.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура создания цели
    """
    keyboard = [
        [InlineKeyboardButton("🎯 Цель на день", callback_data="create_daily_goal")],
        [InlineKeyboardButton("📅 Цель на неделю", callback_data="create_weekly_goal")],
        [InlineKeyboardButton("🗓️ Цель на месяц", callback_data="create_monthly_goal")],
        [InlineKeyboardButton("← Назад к целям", callback_data="my_goals")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_goal_confirmation_keyboard(goal_id: str, action: str) -> InlineKeyboardMarkup:
    """
    Создание клавиатуры подтверждения действия с целью.
    
    Args:
        goal_id: ID цели
        action: Действие (complete, delete, postpone)
        
    Returns:
        InlineKeyboardMarkup: Клавиатура подтверждения
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data=f"goal_{action}_confirm_{goal_id}"),
            InlineKeyboardButton("❌ Нет", callback_data=f"goal_{action}_cancel_{goal_id}")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_goal_priority_keyboard() -> InlineKeyboardMarkup:
    """
    Создание клавиатуры выбора приоритета цели.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура приоритетов
    """
    keyboard = [
        [InlineKeyboardButton("🔴 Высокий", callback_data="goal_priority_high")],
        [InlineKeyboardButton("🟡 Средний", callback_data="goal_priority_medium")],
        [InlineKeyboardButton("🟢 Низкий", callback_data="goal_priority_low")],
        [InlineKeyboardButton("← Назад", callback_data="create_goal")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_goal_deadline_keyboard() -> InlineKeyboardMarkup:
    """
    Создание клавиатуры выбора дедлайна цели.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура дедлайнов
    """
    keyboard = [
        [InlineKeyboardButton("📅 Сегодня", callback_data="goal_deadline_today")],
        [InlineKeyboardButton("📅 Завтра", callback_data="goal_deadline_tomorrow")],
        [InlineKeyboardButton("📅 Через неделю", callback_data="goal_deadline_week")],
        [InlineKeyboardButton("📅 Через месяц", callback_data="goal_deadline_month")],
        [InlineKeyboardButton("⏰ Без дедлайна", callback_data="goal_deadline_none")],
        [InlineKeyboardButton("← Назад", callback_data="create_goal")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_goals_filter_keyboard() -> InlineKeyboardMarkup:
    """
    Создание клавиатуры фильтрации целей.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура фильтров
    """
    keyboard = [
        [InlineKeyboardButton("🎯 Все цели", callback_data="goals_filter_all")],
        [InlineKeyboardButton("⏰ Активные", callback_data="goals_filter_active")],
        [InlineKeyboardButton("✅ Выполненные", callback_data="goals_filter_completed")],
        [InlineKeyboardButton("❌ Просроченные", callback_data="goals_filter_overdue")],
        [InlineKeyboardButton("← Назад к целям", callback_data="my_goals")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


