"""
Сервис для работы с Telegram API.

Содержит методы для отправки сообщений, работы с группами и каналами.
"""

from datetime import datetime
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
        # Кэш для проверки подписки (user_id -> (is_subscribed, timestamp))
        self.subscription_cache = {}
        self.cache_ttl = 300  # 5 минут
    
    def clear_subscription_cache(self, user_id: int = None):
        """
        Очистка кэша подписки.
        
        Args:
            user_id: ID пользователя для очистки конкретной записи, None для очистки всего кэша
        """
        if user_id:
            self.subscription_cache.pop(user_id, None)
            logger.info(f"Очищен кэш подписки для пользователя {user_id}")
        else:
            self.subscription_cache.clear()
            logger.info("Очищен весь кэш подписки")
    
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
            logger.info(f"Сообщение отправлено пользователю {chat_id}")
            return True
        except TelegramError as e:
            # Более детальная обработка ошибок
            if "bot can't initiate conversation" in str(e):
                logger.warning(f"Пользователь {chat_id} не писал боту первым - пропускаем отправку")
            elif "chat not found" in str(e):
                logger.warning(f"Чат {chat_id} не найден - пользователь заблокировал бота или удалил аккаунт")
            elif "blocked" in str(e).lower():
                logger.warning(f"Пользователь {chat_id} заблокировал бота")
            else:
                logger.error(f"Ошибка отправки сообщения пользователю {chat_id}: {e}")
            return False
    
    async def send_welcome_message(self, user_id: int, username: str) -> bool:
        """Отправка приветственного сообщения согласно ТЗ."""
        message = f"""
🔥 Добро пожаловать в клуб «ОСНОВА ПУТИ»!

Привет, {username}! 👋

Ты попал в закрытый клуб людей, которые:
• Берут ответственность за свою жизнь
• Работают над собой каждый день  
• Достигают амбициозных целей
• Поддерживают друг друга в развитии

Что тебя ждет в клубе:
🧘 Ритуалы ЯДРА для дисциплины
📝 Ежедневные отчеты (21:00)
🎯 Еженедельные цели и их достижение
💬 Поддержка активного сообщества
📊 Анализ твоей активности

Для доступа к клубу необходимо:
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
    
    async def send_subscription_active_message(
        self, 
        user_id: int, 
        username: str, 
        subscription_until: datetime,
        reply_to_message=None
    ) -> bool:
        """Отправка сообщения для пользователей с активной подпиской."""
        message = f"""
🎉 Добро пожаловать обратно, {username}!

Твоя подписка на клуб «ОСНОВА ПУТИ» активна до {subscription_until.strftime('%d.%m.%Y')}.

Продолжай свой путь к трансформации! 💪

Что тебя ждет в клубе:
📝 Ежедневные отчеты (21:00)
🎯 Еженедельные цели (воскресенье)
💬 Доступ к закрытой группе
📊 Анализ активности

Все функции работают автоматически. Просто следи за уведомлениями!
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Группа клуба", url="https://t.me/+hWoFGCMcaI83YTY0")],
            [InlineKeyboardButton("ℹ️ О клубе", callback_data="about_club")]
        ])
        
        if reply_to_message:
            # Если есть сообщение для ответа, используем reply_text
            try:
                await reply_to_message.reply_text(message, reply_markup=keyboard)
                return True
            except Exception as e:
                logger.error(f"Ошибка отправки reply сообщения: {e}")
                return False
        else:
            return await self.send_message(user_id, message, keyboard)
    
    async def send_payment_required_message(self, user_id: int, reply_to_message=None) -> bool:
        """Отправка сообщения о необходимости оплаты."""
        message = """
💳 Требуется оплата участия

У тебя нет активной подписки на клуб.

Что даст оплаченное участие:
🧘 Ежедневные ритуалы ЯДРА
📝 Система отчетности (21:00)
🎯 Еженедельные цели
💬 Доступ к закрытой группе
📊 Анализ активности

Готов оплатить доступ?
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Оплатить участие", callback_data="payment_options")],
            [InlineKeyboardButton("ℹ️ О клубе", callback_data="about_club")]
        ])
        
        if reply_to_message:
            # Если есть сообщение для ответа, используем reply_text
            try:
                await reply_to_message.reply_text(message, reply_markup=keyboard)
                return True
            except Exception as e:
                logger.error(f"Ошибка отправки reply сообщения: {e}")
                return False
        else:
            return await self.send_message(user_id, message, keyboard)
    
    async def send_report_reminder(self, user_id: int) -> bool:
        """Отправка напоминания об отчете согласно ТЗ."""
        message = """
📊 Время подвести итог дня

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
📘 О клубе «ОСНОВА ПУТИ»

Что такое ЯДРО?
Это закрытое сообщество людей, которые серьёзно относятся к своему развитию и готовы работать над собой каждый день.

Принципы клуба:
🔥 Дисциплина превыше всего
📈 Постоянный рост и развитие  
💪 Взаимная поддержка и мотивация
🎯 Фокус на результатах
⚡ Активность и вовлеченность

Что даёт участие:
• Ежедневные ритуалы ЯДРА для поддержания дисциплины
• Система отчетности для отслеживания прогресса
• Еженедельные цели и их достижение
• Поддержка единомышленников
• Анализ активности и мотивация

Правила клуба:
1️⃣ Обязательная подписка на основной канал
2️⃣ Активное участие в отчетности
3️⃣ Уважение к другим участникам
4️⃣ Фокус на развитии, а не на жалобах

Стоимость участия:
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
    
    async def send_about_club_message_for_subscribers(self, user_id: int) -> bool:
        """Отправка информации о клубе для пользователей с активной подпиской."""
        message = """
📘 О клубе «ОСНОВА ПУТИ»

Что такое ЯДРО?
Это закрытое сообщество людей, которые серьёзно относятся к своему развитию и готовы работать над собой каждый день.

Принципы клуба:
🔥 Дисциплина превыше всего
📈 Постоянный рост и развитие  
💪 Взаимная поддержка и мотивация
🎯 Фокус на результатах
⚡ Активность и вовлеченность

Что даёт участие:
• Ежедневные отчеты (21:00) для отслеживания прогресса
• Еженедельные цели и их достижение
• Поддержка единомышленников
• Анализ активности и мотивация

Правила клуба:
1️⃣ Обязательная подписка на основной канал
2️⃣ Активное участие в отчетности
3️⃣ Уважение к другим участникам
4️⃣ Фокус на развитии, а не на жалобах

Ты уже часть ЯДРА! Продолжай работу над собой! 💪
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Группа клуба", url="https://t.me/+hWoFGCMcaI83YTY0")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
        ])
        
        return await self.send_message(user_id, message, keyboard)
    
    async def send_goal_reminder(self, user_id: int) -> bool:
        """Отправка напоминания о фиксации недели (воскресенье)."""
        message = """
🎯 Фиксация недели

Воскресенье - время подвести итоги прошедшей недели и поставить цели на следующую.

Ответь на вопросы:
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
📈 Отчет об активности

Статистика за неделю:
• Активных участников: {stats.get('active_count', 0)}
• Неактивных участников: {stats.get('inactive_count', 0)}
• Общая активность: {stats.get('activity_percentage', 0)}%

Топ активных:
{stats.get('top_users', 'Нет данных')}

Подключающиеся:
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
📊 Еженедельный анализ активности

Топ включённых: {top_active_str}
Подключаемся: {connecting_str}

Продолжаем держать ритм! 💪
"""
        
        # Отправляем в группу клуба, если указана
        if settings.GROUP_ID:
            return await self.send_message(int(settings.GROUP_ID), message)
        return False
    
    async def send_message_to_group(self, message: str) -> bool:
        """Отправка сообщения в группу."""
        from config.settings import get_settings
        settings = get_settings()
        if settings.GROUP_ID:
            return await self.send_message(int(settings.GROUP_ID), message)
        return False
    
    async def create_group_invite_link(self, expire_date=None, member_limit=None) -> str:
        """
        Создание пригласительной ссылки для группы.
        
        Args:
            expire_date: Дата истечения ссылки (datetime)
            member_limit: Максимальное количество участников
            
        Returns:
            str: Пригласительная ссылка
        """
        try:
            from config.settings import get_settings
            settings = get_settings()
            
            if not settings.GROUP_ID:
                logger.error("GROUP_ID не настроен")
                return None
                
            # Создаем пригласительную ссылку
            invite_link = await self.bot.create_chat_invite_link(
                chat_id=int(settings.GROUP_ID),
                expire_date=expire_date,
                member_limit=member_limit
            )
            
            logger.info(f"Создана пригласительная ссылка для группы {settings.GROUP_ID}")
            return invite_link.invite_link
            
        except Exception as e:
            logger.error(f"Ошибка создания пригласительной ссылки: {e}")
            return None
    
    async def send_message(self, user_id: int, message: str, keyboard=None, parse_mode="HTML") -> bool:
        """
        Отправка сообщения пользователю.
        
        Args:
            user_id: ID пользователя
            message: Текст сообщения
            keyboard: Клавиатура (опционально)
            parse_mode: Режим парсинга (HTML или Markdown)
            
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
                parse_mode=parse_mode,
                reply_markup=keyboard
            )
            
            logger.info(f"Сообщение отправлено пользователю {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
            return False
    
    async def check_user_subscription(self, user_id: int) -> bool:
        """Проверка подписки пользователя на группу "ЯДРО КЛУБА / ОСНОВА PUTИ" согласно ТЗ."""
        try:
            # Проверяем кэш
            import time
            current_time = time.time()
            if user_id in self.subscription_cache:
                is_subscribed, timestamp = self.subscription_cache[user_id]
                if current_time - timestamp < self.cache_ttl:
                    logger.info(f"🔍 Используем кэшированную проверку подписки для пользователя {user_id}: {is_subscribed}")
                    return is_subscribed
            
            # Реальная проверка подписки на группу "ЯДРО КЛУБА / ОСНОВА PUTИ"
            from config.settings import get_settings
            settings = get_settings()
            group_id = settings.GROUP_ID
            logger.info(f"🔍 Проверяем подписку пользователя {user_id} на группу {group_id}")
            
            # Получаем информацию о пользователе в группе через Bot API
            chat_member = await self.bot.get_chat_member(
                chat_id=group_id,
                user_id=user_id
            )
            
            # Проверяем статус: member, administrator, creator = подписан
            # left, kicked = не подписан
            is_subscribed = chat_member.status in ['member', 'administrator', 'creator']
            
            # Сохраняем в кэш
            self.subscription_cache[user_id] = (is_subscribed, current_time)
            
            logger.info(f"Проверка подписки пользователя {user_id} на группу {group_id}: статус '{chat_member.status}', подписан: {is_subscribed}")
            return is_subscribed
            
        except TelegramError as e:
            logger.error(f"Ошибка проверки подписки пользователя {user_id} на группу {group_id}: {e}")
            # В случае ошибки (например, бот не админ канала) считаем, что не подписан
            # Сохраняем результат ошибки в кэш на короткое время
            self.subscription_cache[user_id] = (False, current_time)
            return False
    
    async def send_subscription_required_message(self, user_id: int) -> bool:
        """Отправка сообщения о необходимости присоединения к группе "ЯДРО КЛУБА / ОСНОВА PUTИ"."""
        message = """
🔒 Требуется участие в группе

Для доступа к клубу «ОСНОВА ПУТИ» необходимо присоединиться к основной группе:
ЯДРО КЛУБА / ОСНОВА PUTИ

Что вас ждет в группе:
• Дисциплина. Энергия. Движение
• Без воды. Без гуру. Без масок  
• Только ты, реальность и направление

После присоединения нажмите "Проверить подписку".
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👥 Присоединиться", url="https://t.me/+hWoFGCMcaI83YTY0")],
            [InlineKeyboardButton("✅ Проверить подписку", callback_data="check_subscription")]
        ])
        
        return await self.send_message(user_id, message, keyboard)
    
    async def send_payment_message(self, user_id: int, amount: int, description: str) -> bool:
        """Отправка сообщения о платеже."""
        message = f"""
💳 Оплата подписки

Сумма: {amount} ₽
Описание: {description}

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
✅ Оплата прошла успешно!

Добро пожаловать в клуб «ОСНОВА ПУТИ»!

🎯 Что дальше:
• Доступ к закрытой группе клуба
• Ежедневные отчеты (21:00)
• Еженедельные цели (воскресенье)
• Анализ активности и мотивация

Все функции работают автоматически. Следи за уведомлениями!

Наслаждайся путешествием! 🚀
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Группа клуба", url="https://t.me/+hWoFGCMcaI83YTY0")],
            [InlineKeyboardButton("ℹ️ О клубе", callback_data="about_club")]
        ])
        
        return await self.send_message(user_id, message, keyboard)
    
    async def send_payment_failed_message(self, user_id: int) -> bool:
        """Отправка сообщения о неудачной оплате."""
        message = """
❌ Оплата не прошла

Попробуй еще раз или выбери другой способ оплаты.

Если проблема повторяется, обратись в поддержку.
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data="payment_retry")],
            [InlineKeyboardButton("🆘 Поддержка", callback_data="support")]
        ])
        
        return await self.send_message(user_id, message, keyboard)




