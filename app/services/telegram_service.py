"""
Сервис для работы с Telegram API.

Содержит методы для отправки сообщений, работы с группами и каналами.
"""

from typing import Optional, List, Dict, Any
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import TelegramError
from loguru import logger

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import settings


class TelegramService:
    """Сервис для работы с Telegram API."""
    
    def __init__(self, bot: Bot):
        """Инициализация сервиса."""
        self.bot = bot
    
    async def send_message(
        self, 
        chat_id: int, 
        text: str, 
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        parse_mode: str = "HTML"
    ) -> bool:
        """Отправка сообщения в чат."""
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            return True
        except TelegramError as e:
            logger.error(f"Ошибка отправки сообщения в {chat_id}: {e}")
            return False
    
    async def send_welcome_message(self, user_id: int, username: str) -> bool:
        """Отправка приветственного сообщения."""
        message = f"""
🎉 <b>Добро пожаловать в клуб «ОСНОВА ПУТИ»!</b>

Привет, {username}! 👋

Ты присоединился к сообществу людей, которые:
• Работают над собой каждый день
• Достигают поставленных целей
• Поддерживают друг друга в развитии

<b>Что тебя ждет:</b>
🧘 Ежедневные ритуалы ЯДРА
📝 Еженедельные отчеты
🎯 Постановка и достижение целей
💬 Поддержка сообщества

Готов начать путь к лучшей версии себя? 🚀
"""
        
        # Создаем клавиатуру
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Начать", callback_data="start_journey")],
            [InlineKeyboardButton("ℹ️ О клубе", callback_data="about_club")],
            [InlineKeyboardButton("💳 Подписка", callback_data="subscription")]
        ])
        
        return await self.send_message(user_id, message, keyboard)
    
    async def send_report_reminder(self, user_id: int) -> bool:
        """Отправка напоминания об отчете."""
        message = """
📊 <b>Время подвести итог дня</b>

Напиши, что прожил, что понял, где дотянул, где сдался.

Это поможет тебе:
• Осознать свой прогресс
• Выявить точки роста
• Сохранить мотивацию
• Остаться в ритме

Готов поделиться?
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Отчёт отправлен", callback_data="report_submitted")],
            [InlineKeyboardButton("🧩 Не готов делиться", callback_data="report_skip")]
        ])
        
        return await self.send_message(user_id, message, keyboard)
    
    async def send_goal_reminder(self, user_id: int) -> bool:
        """Отправка напоминания о цели."""
        message = """
🎯 <b>Цель на неделю</b>

Какая твоя цель на эту неделю? Одно действие, которое продвинет тебя на 10 шагов вперёд.
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎯 Поставить цель", callback_data="set_goal")],
            [InlineKeyboardButton("⏭️ Пропустить", callback_data="skip_goal")]
        ])
        
        return await self.send_message(user_id, message, keyboard)
    
    async def send_ritual_message(
        self, 
        user_id: int, 
        ritual_type: str, 
        message: str,
        buttons: List[Dict[str, str]]
    ) -> bool:
        """Отправка сообщения о ритуале."""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(btn["text"], callback_data=btn["callback"])]
            for btn in buttons
        ])
        
        return await self.send_message(user_id, message, keyboard)
    
    async def send_warmup_message(
        self, 
        user_id: int, 
        message: str,
        buttons: Optional[List[Dict[str, str]]] = None
    ) -> bool:
        """Отправка сообщения прогрева."""
        keyboard = None
        if buttons:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(btn["text"], callback_data=btn["callback"])]
                for btn in buttons
            ])
        
        return await self.send_message(user_id, message, keyboard)
    
    async def send_admin_activity_report(self, stats: Dict[str, Any]) -> bool:
        """Отправка отчета об активности админу."""
        message = f"""
📈 <b>Отчет об активности</b>

<b>Статистика за неделю:</b>
• Активных участников: {stats.get('active_count', 0)}
• Неактивных участников: {stats.get('inactive_count', 0)}
• Общая активность: {stats.get('activity_percentage', 0)}%

<b>Топ активных:</b>
{stats.get('top_users', 'Нет данных')}

<b>Подключающиеся:</b>
{stats.get('inactive_users', 'Нет данных')}
"""
        
        return await self.send_message(settings.SUPER_ADMIN_ID, message)
    
    async def send_public_activity_report(self, stats: Dict[str, Any]) -> bool:
        """Отправка публичного отчета об активности."""
        message = f"""
📊 <b>Анализ активности участников</b>

<b>Топ включённых:</b> {stats.get('active_users', 'Нет данных')}
<b>Подключаемся:</b> {stats.get('inactive_users', 'Нет данных')}

Статистика за неделю:
• Активных участников: {stats.get('active_count', 0)}
• Неактивных участников: {stats.get('inactive_count', 0)}
• Общая активность: {stats.get('activity_percentage', 0)}%
"""
        
        # Отправляем в группу, если указана
        if settings.GROUP_ID:
            return await self.send_message(int(settings.GROUP_ID), message)
        return False
    
    async def send_message_to_group(self, message: str) -> bool:
        """Отправка сообщения в группу."""
        if settings.GROUP_ID:
            return await self.send_message(int(settings.GROUP_ID), message)
        return False
    
    async def check_user_subscription(self, user_id: int) -> bool:
        """Проверка подписки пользователя на канал."""
        if not settings.CHANNEL_ID:
            return True  # Если канал не настроен, считаем что подписка есть
        
        try:
            member = await self.bot.get_chat_member(
                chat_id=int(settings.CHANNEL_ID),
                user_id=user_id
            )
            return member.status in ['member', 'administrator', 'creator']
        except TelegramError as e:
            logger.error(f"Ошибка проверки подписки для {user_id}: {e}")
            return False
    
    async def send_subscription_required_message(self, user_id: int) -> bool:
        """Отправка сообщения о необходимости подписки."""
        message = f"""
🔒 <b>Требуется подписка</b>

Для доступа к функциям клуба необходимо подписаться на канал:
@{settings.CHANNEL_USERNAME}

После подписки нажми кнопку "Проверить подписку".
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Подписаться", url=f"https://t.me/{settings.CHANNEL_USERNAME}")],
            [InlineKeyboardButton("✅ Проверить подписку", callback_data="check_subscription")]
        ])
        
        return await self.send_message(user_id, message, keyboard)
    
    async def send_payment_message(self, user_id: int, amount: int, description: str) -> bool:
        """Отправка сообщения о платеже."""
        message = f"""
💳 <b>Оплата подписки</b>

<b>Сумма:</b> {amount} ₽
<b>Описание:</b> {description}

Выберите способ оплаты:
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Банковская карта", callback_data="payment_card")],
            [InlineKeyboardButton("📱 СБП", callback_data="payment_sbp")],
            [InlineKeyboardButton("💰 Электронные кошельки", callback_data="payment_wallet")],
            [InlineKeyboardButton("❌ Отмена", callback_data="payment_cancel")]
        ])
        
        return await self.send_message(user_id, message, keyboard)
    
    async def send_payment_success_message(self, user_id: int) -> bool:
        """Отправка сообщения об успешной оплате."""
        message = """
✅ <b>Оплата прошла успешно!</b>

Добро пожаловать в клуб «ОСНОВА ПУТИ»!

🎯 <b>Что дальше:</b>
• Ты получишь доступ к закрытому чату
• Будешь получать ежедневные ритуалы ЯДРА
• Сможешь участвовать в еженедельных отчетах
• Получишь персональную поддержку

Наслаждайся путешествием! 🚀
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Начать", callback_data="start_journey")]
        ])
        
        return await self.send_message(user_id, message, keyboard)
    
    async def send_payment_failed_message(self, user_id: int) -> bool:
        """Отправка сообщения о неудачной оплате."""
        message = """
❌ <b>Оплата не прошла</b>

Попробуй еще раз или выбери другой способ оплаты.

Если проблема повторяется, обратись в поддержку.
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data="payment_retry")],
            [InlineKeyboardButton("🆘 Поддержка", callback_data="support")]
        ])
        
        return await self.send_message(user_id, message, keyboard)



