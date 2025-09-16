"""
Клавиатуры для админ панели ClubBot.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Получить основную клавиатуру админ панели."""
    keyboard = [
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton("💳 Платежи", callback_data="admin_payments")],
        [InlineKeyboardButton("📊 Отчеты", callback_data="admin_reports")],
        [InlineKeyboardButton("🧘 Ритуалы", callback_data="admin_rituals")],
        [InlineKeyboardButton("🎯 Цели", callback_data="admin_goals")],
        [InlineKeyboardButton("📈 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="admin_settings")],
        [InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_users_admin_keyboard() -> InlineKeyboardMarkup:
    """Получить клавиатуру управления пользователями."""
    keyboard = [
        [InlineKeyboardButton("📋 Список пользователей", callback_data="admin_users_list")],
        [InlineKeyboardButton("🔍 Поиск пользователя", callback_data="admin_users_search")],
        [InlineKeyboardButton("📊 Статистика пользователей", callback_data="admin_users_stats")],
        [InlineKeyboardButton("👥 Активные пользователи", callback_data="admin_users_active")],
        [InlineKeyboardButton("⏰ Истекающие подписки", callback_data="admin_users_expiring")],
        [InlineKeyboardButton("🔙 К админ панели", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_payments_admin_keyboard() -> InlineKeyboardMarkup:
    """Получить клавиатуру управления платежами."""
    keyboard = [
        [InlineKeyboardButton("💳 Все платежи", callback_data="admin_payments_list")],
        [InlineKeyboardButton("✅ Успешные платежи", callback_data="admin_payments_success")],
        [InlineKeyboardButton("❌ Неудачные платежи", callback_data="admin_payments_failed")],
        [InlineKeyboardButton("📊 Статистика платежей", callback_data="admin_payments_stats")],
        [InlineKeyboardButton("💰 Доходы", callback_data="admin_payments_revenue")],
        [InlineKeyboardButton("🔙 К админ панели", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_reports_admin_keyboard() -> InlineKeyboardMarkup:
    """Получить клавиатуру управления отчетами."""
    keyboard = [
        [InlineKeyboardButton("📋 Все отчеты", callback_data="admin_reports_list")],
        [InlineKeyboardButton("📊 Статистика отчетов", callback_data="admin_reports_stats")],
        [InlineKeyboardButton("👥 Активные авторы", callback_data="admin_reports_authors")],
        [InlineKeyboardButton("⏰ Просроченные отчеты", callback_data="admin_reports_overdue")],
        [InlineKeyboardButton("🔙 К админ панели", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_rituals_admin_keyboard() -> InlineKeyboardMarkup:
    """Получить клавиатуру управления ритуалами."""
    keyboard = [
        [InlineKeyboardButton("🧘 Список ритуалов", callback_data="admin_rituals_list")],
        [InlineKeyboardButton("➕ Создать ритуал", callback_data="admin_rituals_create")],
        [InlineKeyboardButton("📊 Статистика ритуалов", callback_data="admin_rituals_stats")],
        [InlineKeyboardButton("⏰ Настройки времени", callback_data="admin_rituals_schedule")],
        [InlineKeyboardButton("🔙 К админ панели", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_goals_admin_keyboard() -> InlineKeyboardMarkup:
    """Получить клавиатуру управления целями."""
    keyboard = [
        [InlineKeyboardButton("🎯 Все цели", callback_data="admin_goals_list")],
        [InlineKeyboardButton("📊 Статистика целей", callback_data="admin_goals_stats")],
        [InlineKeyboardButton("✅ Выполненные цели", callback_data="admin_goals_completed")],
        [InlineKeyboardButton("⏰ Просроченные цели", callback_data="admin_goals_overdue")],
        [InlineKeyboardButton("🔙 К админ панели", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_stats_admin_keyboard() -> InlineKeyboardMarkup:
    """Получить клавиатуру статистики."""
    keyboard = [
        [InlineKeyboardButton("📊 Общая статистика", callback_data="admin_stats_general")],
        [InlineKeyboardButton("👥 Статистика пользователей", callback_data="admin_stats_users")],
        [InlineKeyboardButton("💳 Статистика платежей", callback_data="admin_stats_payments")],
        [InlineKeyboardButton("📈 Активность", callback_data="admin_stats_activity")],
        [InlineKeyboardButton("📅 Отчеты по периодам", callback_data="admin_stats_periods")],
        [InlineKeyboardButton("🔙 К админ панели", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_settings_admin_keyboard() -> InlineKeyboardMarkup:
    """Получить клавиатуру настроек."""
    keyboard = [
        [InlineKeyboardButton("⚙️ Основные настройки", callback_data="admin_settings_main")],
        [InlineKeyboardButton("👥 Управление админами", callback_data="admin_settings_admins")],
        [InlineKeyboardButton("💳 Настройки платежей", callback_data="admin_settings_payments")],
        [InlineKeyboardButton("🧘 Настройки ритуалов", callback_data="admin_settings_rituals")],
        [InlineKeyboardButton("📊 Настройки отчетов", callback_data="admin_settings_reports")],
        [InlineKeyboardButton("🔙 К админ панели", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_user_actions_keyboard(user_id: str) -> InlineKeyboardMarkup:
    """Получить клавиатуру действий с пользователем."""
    keyboard = [
        [InlineKeyboardButton("👁️ Просмотр профиля", callback_data=f"admin_user_view_{user_id}")],
        [InlineKeyboardButton("📊 Статистика", callback_data=f"admin_user_stats_{user_id}")],
        [InlineKeyboardButton("💳 Подписки", callback_data=f"admin_user_subscriptions_{user_id}")],
        [InlineKeyboardButton("📝 Отчеты", callback_data=f"admin_user_reports_{user_id}")],
        [InlineKeyboardButton("🧘 Ритуалы", callback_data=f"admin_user_rituals_{user_id}")],
        [InlineKeyboardButton("🎯 Цели", callback_data=f"admin_user_goals_{user_id}")],
        [InlineKeyboardButton("⚠️ Заблокировать", callback_data=f"admin_user_ban_{user_id}")],
        [InlineKeyboardButton("🔙 К списку пользователей", callback_data="admin_users_list")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_pagination_keyboard(current_page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
    """Получить клавиатуру пагинации."""
    keyboard = []
    
    # Кнопки навигации
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"{prefix}_page_{current_page - 1}"))
    
    nav_buttons.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="noop"))
    
    if current_page < total_pages:
        nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"{prefix}_page_{current_page + 1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    return InlineKeyboardMarkup(keyboard)


def get_confirm_keyboard(action: str, item_id: str) -> InlineKeyboardMarkup:
    """Получить клавиатуру подтверждения действия."""
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data=f"admin_confirm_{action}_{item_id}")],
        [InlineKeyboardButton("❌ Отменить", callback_data=f"admin_cancel_{action}_{item_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)
