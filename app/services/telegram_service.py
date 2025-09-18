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
        """Отправка приветственного сообщения согласно ТЗ."""
        message = f"""
🔥 <b>Добро пожаловать в клуб «ОСНОВА ПУТИ»!</b>

Привет, {username}! 👋

Ты попал в закрытый клуб людей, которые:
• Берут ответственность за свою жизнь
• Работают над собой каждый день  
• Достигают амбициозных целей
• Поддерживают друг друга в развитии

<b>Что тебя ждет в клубе:</b>
🧘 Ритуалы ЯДРА для дисциплины
📝 Ежедневные отчеты (21:00)
🎯 Еженедельные цели и их достижение
💬 Поддержка активного сообщества
📊 Анализ твоей активности

<b>Для доступа к клубу необходимо:</b>
1️⃣ Подписаться на основной канал
2️⃣ Оплатить участие в клубе
3️⃣ Соблюдать правила активности

Готов присоединиться к ЯДРУ? 🚀
"""
        
        # Создаем клавиатуру согласно ТЗ
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Проверить подписку", callback_data="check_subscription")],
            [InlineKeyboardButton("💳 Оплатить доступ", callback_data="payment_options")],
            [InlineKeyboardButton("📘 Узнать о клубе", callback_data="about_club")]
        ])
        
        return await self.send_message(user_id, message, keyboard)
    
    async def send_report_reminder(self, user_id: int) -> bool:
        """Отправка напоминания об отчете согласно ТЗ."""
        message = """
📊 <b>Время подвести итог дня</b>

Напиши, что прожил, что понял, где дотянул, где сдался.

Можешь отвечать текстом или нажать кнопку:
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Отчёт отправлен", callback_data="report_submitted")],
            [InlineKeyboardButton("🧩 Не готов делиться", callback_data="report_skip")]
        ])
        
        return await self.send_message(user_id, message, keyboard)
    
    async def send_about_club_message(self, user_id: int) -> bool:
        """Отправка информации о клубе согласно ТЗ."""
        message = """
📘 <b>О клубе «ОСНОВА ПУТИ»</b>

<b>Что такое ЯДРО?</b>
Это закрытое сообщество людей, которые серьёзно относятся к своему развитию и готовы работать над собой каждый день.

<b>Принципы клуба:</b>
🔥 Дисциплина превыше всего
📈 Постоянный рост и развитие  
💪 Взаимная поддержка и мотивация
🎯 Фокус на результатах
⚡ Активность и вовлеченность

<b>Что даёт участие:</b>
• Ежедневные ритуалы ЯДРА для поддержания дисциплины
• Система отчетности для отслеживания прогресса
• Еженедельные цели и их достижение
• Поддержка единомышленников
• Анализ активности и мотивация

<b>Правила клуба:</b>
1️⃣ Обязательная подписка на основной канал
2️⃣ Активное участие в отчетности
3️⃣ Уважение к другим участникам
4️⃣ Фокус на развитии, а не на жалобах

<b>Стоимость участия:</b>
💎 1 месяц - 2990₽
💎 3 месяца - 7990₽ (скидка 10%)
💎 Подписка - 29990₽ (скидка 15%)

Готов стать частью ЯДРА? 💪
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Проверить подписку", callback_data="check_subscription")],
            [InlineKeyboardButton("💳 Оплатить доступ", callback_data="payment_options")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
        ])
        
        return await self.send_message(user_id, message, keyboard)
    
    async def send_goal_reminder(self, user_id: int) -> bool:
        """Отправка напоминания о фиксации недели (воскресенье)."""
        message = """
🎯 <b>Фиксация недели</b>

Воскресенье - время подвести итоги прошедшей недели и поставить цели на следующую.

<b>Ответь на вопросы:</b>
• Что удалось достичь на этой неделе?
• Какие были главные инсайты?
• Что не получилось и почему?
• Какая главная цель на следующую неделю?

Напиши свою фиксацию недели или нажми кнопку:
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Фиксация отправлена", callback_data="goal_submitted")],
            [InlineKeyboardButton("⏭️ Пропустить", callback_data="goal_skip")]
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
        """Отправка публичного отчета об активности согласно ТЗ."""
        # Формируем список топ активных пользователей
        top_active = stats.get('top_active', [])
        top_active_str = ", ".join([f"@{user}" for user in top_active[:3]]) if top_active else "Нет данных"
        
        # Формируем список подключающихся пользователей  
        connecting = stats.get('connecting', [])
        connecting_str = ", ".join([f"@{user}" for user in connecting[:3]]) if connecting else "Нет данных"
        
        message = f"""
📊 <b>Еженедельный анализ активности</b>

<b>Топ включённых:</b> {top_active_str}
<b>Подключаемся:</b> {connecting_str}

Продолжаем держать ритм! 💪
"""
        
        # Отправляем в группу клуба, если указана
        if settings.GROUP_ID:
            return await self.send_message(int(settings.GROUP_ID), message)
        return False
    
    async def send_message_to_group(self, message: str) -> bool:
        """Отправка сообщения в группу."""
        if settings.GROUP_ID:
            return await self.send_message(int(settings.GROUP_ID), message)
        return False
    
    async def send_message(self, user_id: int, message: str, keyboard=None) -> bool:
        """
        Отправка сообщения пользователю.
        
        Args:
            user_id: ID пользователя
            message: Текст сообщения
            keyboard: Клавиатура (опционально)
            
        Returns:
            bool: True если сообщение отправлено успешно
        """
        try:
            if not self.bot:
                logger.error("Bot не инициализирован")
                return False
                
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            
            logger.info(f"Сообщение отправлено пользователю {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
            return False
    
    async def check_user_subscription(self, user_id: int) -> bool:
        """Проверка подписки пользователя на канал @osnovaputi согласно ТЗ."""
        try:
            # 🚧 ВРЕМЕННАЯ ЗАГЛУШКА для тестирования CryptoBot
            # TODO: Убрать после добавления бота как админа в @osnovaputi
            logger.info(f"🧪 ЗАГЛУШКА: Пользователь {user_id} считается подписанным на @osnovaputi")
            return True
            
            # Закомментированный рабочий код (раскомментировать после настройки канала):
            """
            # Проверяем подписку на основной канал @osnovaputi
            channel_username = "@osnovaputi"
            
            # Получаем информацию о пользователе в канале через Bot API
            chat_member = await self.bot.get_chat_member(
                chat_id=channel_username,
                user_id=user_id
            )
            
            # Проверяем статус: member, administrator, creator = подписан
            # left, kicked = не подписан
            is_subscribed = chat_member.status in ['member', 'administrator', 'creator']
            
            logger.info(f"Проверка подписки пользователя {user_id} на @osnovaputi: статус '{chat_member.status}', подписан: {is_subscribed}")
            return is_subscribed
            """
            
        except TelegramError as e:
            logger.error(f"Ошибка проверки подписки пользователя {user_id} на @osnovaputi: {e}")
            # В случае ошибки (например, бот не админ канала) считаем, что не подписан
            return False
    
    async def send_subscription_required_message(self, user_id: int) -> bool:
        """Отправка сообщения о необходимости подписки на @osnovaputi."""
        message = """
🔒 <b>Требуется подписка</b>

Для доступа к клубу «ОСНОВА ПУТИ» необходимо подписаться на основной канал:
@osnovaputi

<b>Что вас ждет в канале:</b>
• Дисциплина. Энергия. Движение
• Без воды. Без гуру. Без масок  
• Только ты, реальность и направление

После подписки нажмите "Проверить подписку".
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Подписаться", url="https://t.me/osnovaputi")],
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




