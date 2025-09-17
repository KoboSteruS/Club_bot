"""
Конфигурация для ClubBot - бота для управления участниками платного клуба.
"""

import os
from pathlib import Path
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения для ClubBot."""
    
    # Основные настройки бота
    BOT_TOKEN: str = Field(..., env="BOT_TOKEN")
    BOT_NAME: str = "ОСНОВА ПУТИ - ClubBot"
    BOT_DESCRIPTION: str = "Бот для управления участниками платного клуба"
    
    # Настройки базы данных
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./club.db", env="DATABASE_URL")
    
    # Настройки канала/группы
    CHANNEL_ID: str = Field(default="@osnovaputi", env="CHANNEL_ID")
    CHANNEL_USERNAME: str = Field(default="osnovaputi", env="CHANNEL_USERNAME")
    GROUP_ID: str = Field(default="", env="GROUP_ID")  # ID группы клуба
    
    # Настройки админов
    ADMIN_IDS: str = Field(default="1670311707", env="ADMIN_IDS")
    SUPER_ADMIN_ID: int = Field(default=1670311707, env="SUPER_ADMIN_ID")
    
    @property
    def admin_ids_list(self) -> List[int]:
        """Получить список ID админов."""
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip()]
    
    # Настройки платежей
    PAYMENT_PROVIDER: str = Field(default="cryptobot", env="PAYMENT_PROVIDER")  # cryptobot, freekassa, telegram
    CRYPTOBOT_TOKEN: str = Field(default="460943:AAu5rpHHNrF2UVVVWIOof9SfeZ2XO1ZpvO3", env="CRYPTOBOT_TOKEN")
    BOT_USERNAME: str = Field(default="osnovapti_bot", env="BOT_USERNAME")
    FREKASSA_MERCHANT_ID: str = Field(default="", env="FREKASSA_MERCHANT_ID")
    FREKASSA_SECRET_KEY: str = Field(default="", env="FREKASSA_SECRET_KEY")
    FREKASSA_API_KEY: str = Field(default="", env="FREKASSA_API_KEY")
    
    # Настройки тарифов
    MONTHLY_PRICE: int = Field(default=2990, env="MONTHLY_PRICE")  # в рублях
    QUARTERLY_PRICE: int = Field(default=7990, env="QUARTERLY_PRICE")  # в рублях
    YEARLY_PRICE: int = Field(default=29990, env="YEARLY_PRICE")  # в рублях
    
    # Настройки напоминаний
    RENEWAL_REMINDER_DAYS: int = Field(default=3, env="RENEWAL_REMINDER_DAYS")
    REPORT_REMINDER_HOUR: int = Field(default=21, env="REPORT_REMINDER_HOUR")
    REPORT_REMINDER_MINUTE: int = Field(default=0, env="REPORT_REMINDER_MINUTE")
    
    # Настройки ритуалов
    MORNING_RITUAL_HOUR: int = Field(default=6, env="MORNING_RITUAL_HOUR")
    MORNING_RITUAL_MINUTE: int = Field(default=30, env="MORNING_RITUAL_MINUTE")
    EVENING_RITUAL_HOUR: int = Field(default=21, env="EVENING_RITUAL_HOUR")
    EVENING_RITUAL_MINUTE: int = Field(default=0, env="EVENING_RITUAL_MINUTE")
    
    # Настройки отчетности
    WEEKLY_REPORT_DAY: int = Field(default=6, env="WEEKLY_REPORT_DAY")  # 6 = воскресенье
    WEEKLY_REPORT_HOUR: int = Field(default=20, env="WEEKLY_REPORT_HOUR")
    
    # Настройки целей
    GOAL_DAY_OF_WEEK: int = Field(default=6, env="GOAL_DAY_OF_WEEK")  # 6 = воскресенье
    
    # Настройки аналитики
    ANALYTICS_DAY_OF_WEEK: int = Field(default=6, env="ANALYTICS_DAY_OF_WEEK")  # 6 = воскресенье
    
    # Настройки логирования
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="logs/clubbot.log", env="LOG_FILE")
    
    # Настройки разработки
    DEBUG: bool = Field(default=False, env="DEBUG")
    TESTING: bool = Field(default=False, env="TESTING")
    ECHO_SQL: bool = Field(default=False, env="ECHO_SQL")
    
    # Настройки планировщика
    SCHEDULER_TIMEZONE: str = Field(default="Europe/Moscow", env="SCHEDULER_TIMEZONE")
    RITUAL_SCHEDULER_ENABLED: bool = Field(default=True, env="RITUAL_SCHEDULER_ENABLED")
    REPORT_SCHEDULER_ENABLED: bool = Field(default=True, env="REPORT_SCHEDULER_ENABLED")
    SUBSCRIPTION_SCHEDULER_ENABLED: bool = Field(default=True, env="SUBSCRIPTION_SCHEDULER_ENABLED")
    
    # Настройки уведомлений
    NOTIFICATION_ENABLED: bool = Field(default=True, env="NOTIFICATION_ENABLED")
    ADMIN_NOTIFICATIONS: bool = Field(default=True, env="ADMIN_NOTIFICATIONS")
    DAILY_STATS_ENABLED: bool = Field(default=True, env="DAILY_STATS_ENABLED")
    
    class Config:
        env_file = Path(__file__).parent.parent / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Создаем глобальный экземпляр настроек
settings = Settings()


# Настройки для ритуалов ЯДРА
class RitualSettings:
    """Настройки ритуалов ЯДРА."""
    
    # Утренние ритуалы
    MORNING_RITUALS = [
        {
            "name": "Благодарность",
            "message": "🌅 <b>Утро. Поблагодари за 3 вещи.</b>\n\nНастройся. Сделай вдох. Сегодня ты выбираешь — быть в себе или потеряться.",
            "buttons": [
                {"text": "✅ Поблагодарил", "callback": "ritual_morning_gratitude"},
                {"text": "🎯 Пишу цель дня", "callback": "ritual_morning_goal"},
                {"text": "🧘 Иду в тишину", "callback": "ritual_morning_meditation"}
            ]
        }
    ]
    
    # Вечерние ритуалы
    EVENING_RITUALS = [
        {
            "name": "Итоги дня",
            "message": "🌙 <b>Вечер. Подведи итог.</b>\n\nЧто получилось? Где провал? Что осознал?",
            "buttons": [
                {"text": "📝 Пишу отчёт", "callback": "ritual_evening_report"},
                {"text": "😐 Пропускаю", "callback": "ritual_evening_skip"},
                {"text": "🧠 Мысль дня", "callback": "ritual_evening_thought"}
            ]
        }
    ]
    
    # Недельные вызовы
    WEEKLY_CHALLENGES = [
        "⚔️ <b>Вызов недели:</b> Один день — без жалоб. Даже мысленных. Попробуй.",
        "⚔️ <b>Вызов недели:</b> Один день — без социальных сетей. Живи реальностью.",
        "⚔️ <b>Вызов недели:</b> Один день — без оправданий. Только действия.",
        "⚔️ <b>Вызов недели:</b> Один день — без критики. Только поддержка.",
        "⚔️ <b>Вызов недели:</b> Один день — без сравнений. Только свой путь."
    ]
    
    # Цели на неделю
    WEEKLY_GOAL_MESSAGE = "🎯 <b>Цель на неделю</b>\n\nКакая твоя цель на эту неделю? Одно действие, которое продвинет тебя на 10 шагов вперёд."
    
    WEEKLY_GOAL_REMINDER = "🎯 <b>Напоминание о цели</b>\n\nТы писал: {goal}\n\nВыполнил?"


# Настройки для отчетности
class ReportSettings:
    """Настройки отчетности."""
    
    # Еженедельные напоминания
    WEEKLY_REMINDER_MESSAGE = """
📊 <b>Время подвести итог дня</b>

Напиши, что прожил, что понял, где дотянул, где сдался.

Это поможет тебе:
• Осознать свой прогресс
• Выявить точки роста
• Сохранить мотивацию
• Остаться в ритме

Готов поделиться?
"""
    
    # Кнопки для отчетов
    REPORT_BUTTONS = [
        {"text": "📝 Отчёт отправлен", "callback": "report_submitted"},
        {"text": "🧩 Не готов делиться", "callback": "report_skip"}
    ]
    
    # Анализ активности
    ACTIVITY_ANALYSIS_MESSAGE = """
📈 <b>Анализ активности участников</b>

<b>Топ включённых:</b> {active_users}
<b>Подключаемся:</b> {inactive_users}

Статистика за неделю:
• Активных участников: {active_count}
• Неактивных участников: {inactive_count}
• Общая активность: {activity_percentage}%
"""


# Настройки для платежей
class PaymentSettings:
    """Настройки платежей."""
    
    # Тарифы
    TARIFFS = {
        "monthly": {
            "name": "1 месяц",
            "price": 2990,
            "currency": "RUB",
            "description": "Доступ к клубу на 1 месяц"
        },
        "quarterly": {
            "name": "3 месяца",
            "price": 7990,
            "currency": "RUB",
            "description": "Доступ к клубу на 3 месяца (скидка 10%)"
        },
        "yearly": {
            "name": "1 год",
            "price": 29990,
            "currency": "RUB",
            "description": "Доступ к клубу на 1 год (скидка 15%)"
        }
    }
    
    # Сообщения о платежах
    PAYMENT_SUCCESS_MESSAGE = """
✅ <b>Оплата прошла успешно!</b>

Добро пожаловать в клуб «ОСНОВА ПУТИ»!

🎯 <b>Что дальше:</b>
• Ты получишь доступ к закрытому чату
• Будешь получать ежедневные ритуалы ЯДРА
• Сможешь участвовать в еженедельных отчетах
• Получишь персональную поддержку

Наслаждайся путешествием! 🚀
"""
    
    PAYMENT_FAILED_MESSAGE = """
❌ <b>Оплата не прошла</b>

Попробуй еще раз или выбери другой способ оплаты.

Если проблема повторяется, обратись в поддержку.
"""
    
    RENEWAL_REMINDER_MESSAGE = """
⏰ <b>Напоминание о продлении</b>

Твоя подписка заканчивается через {days} дней.

Чтобы не потерять доступ к клубу, продли подписку сейчас.

🎯 <b>Преимущества продления:</b>
• Продолжение ритуалов ЯДРА
• Доступ к закрытому чату
• Еженедельные отчеты
• Персональная поддержка

Продлить подписку?
"""


# Создаем глобальные экземпляры настроек
ritual_settings = RitualSettings()
report_settings = ReportSettings()
payment_settings = PaymentSettings()
