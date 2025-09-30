"""
Основной обработчик для ClubBot согласно ТЗ.

Обрабатывает основные callback'ы: проверка подписки, оплата, информация о клубе.
"""

from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger

from app.core.database import get_db_session


async def safe_answer_callback(query, text: str = None) -> bool:
    """
    Безопасный ответ на callback query с обработкой устаревших запросов.
    
    Args:
        query: Callback query объект
        text: Текст для ответа (опционально)
        
    Returns:
        bool: True если ответ отправлен успешно
    """
    try:
        await query.answer(text=text)
        return True
    except Exception as e:
        if "Query is too old" in str(e) or "query id is invalid" in str(e):
            logger.warning(f"Устаревший callback query: {e}")
            return False
        else:
            logger.error(f"Ошибка ответа на callback query: {e}")
            return False
from app.services.user_service import UserService
from app.services.telegram_service import TelegramService
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from config.settings import settings


async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Основной обработчик callback'ов согласно ТЗ.
    
    Args:
        update: Обновление от Telegram
        context: Контекст бота
    """
    try:
        query = update.callback_query
        if not query:
            return
            
        # Безопасный ответ на callback query
        if not await safe_answer_callback(query):
            logger.warning("Пропускаем обработку устаревшего callback query")
            return
        
        user = update.effective_user
        if not user:
            return
        
        callback_data = query.data
        
        if callback_data == "check_subscription":
            await handle_subscription_check(update, context)
        elif callback_data == "payment_options":
            await handle_payment_options(update, context)
        elif callback_data == "about_club":
            await handle_about_club(update, context)
        elif callback_data == "back_to_start":
            await handle_back_to_start(update, context)
        elif callback_data == "subscription_confirmed":
            await handle_subscription_confirmed(update, context)
        elif callback_data.startswith("pay_"):
            await handle_payment_create(update, context)
        elif callback_data.startswith("check_payment_"):
            await handle_payment_check(update, context)
        else:
            await query.edit_message_text("❌ Неизвестная команда")
            
    except Exception as e:
        logger.error(f"Ошибка в main_handler: {e}")
        # Не пытаемся отвечать на callback query в блоке except,
        # так как он уже может быть устаревшим


async def handle_subscription_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка проверки подписки согласно ТЗ."""
    try:
        user = update.effective_user
        telegram_service = TelegramService(context.bot)
        
        # Проверяем подписку на канал
        is_subscribed = await telegram_service.check_user_subscription(user.id)
        
        if is_subscribed:
            # Пользователь подписан
            async with get_db_session() as session:
                user_service = UserService(session)
                db_user = await user_service.get_user_by_telegram_id(user.id)
                
                if db_user:
                    # Обновляем статус подписки
                    from app.schemas.user import UserUpdate
                    await user_service.update_user(str(db_user.id), UserUpdate(
                        is_subscribed_to_channel=True
                    ))
            
            message = """✅ Подписка подтверждена!

Отлично 👊 Ты в основном канале. Это только начало.

Чтобы войти в ЯДРО и получить полный доступ, необходимо оплатить участие.

Что даёт оплаченное участие:
🎯 Постановка месячных целей и их проверка
📝 Еженедельные отчёты — видно, где ты держишь форму, а где сдаёшься
💬 Доступ в закрытый круг без флуда и жалости — только рост и поддержка
🔎 Система наблюдения: твои результаты всегда на виду

Здесь становится ясно, кто готов идти дальше, а кто остаётся в старом.

🚀 Готов оплатить доступ и войти в ЯДРО?"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Оплатить доступ", callback_data="payment_options")],
                [InlineKeyboardButton("📘 Узнать больше", callback_data="about_club")]
            ])
            
        else:
            # Пользователь не подписан
            message = """
❌ <b>Участие в группе не найдено</b>

Для доступа к клубу необходимо присоединиться к основной группе:
ЯДРО КЛУБА / ОСНОВА PUTИ

<b>Что нужно сделать:</b>
1️⃣ Нажми кнопку "Присоединиться"
2️⃣ Присоединись к группе
3️⃣ Вернись сюда и нажми "Проверить снова"

<b>Что вас ждет в группе:</b>
• Дисциплина. Энергия. Движение
• Без воды. Без гуру. Без масок
• Только ты, реальность и направление
• Общение с участниками клуба
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👥 Присоединиться", url="https://t.me/+hWoFGCMcaI83YTY0")],
                [InlineKeyboardButton("🔄 Проверить снова", callback_data="check_subscription")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ])
        
        await update.callback_query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в handle_subscription_check: {e}")
        await update.callback_query.answer("❌ Произошла ошибка при проверке подписки")


async def handle_payment_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка выбора вариантов оплаты."""
    try:
        message = """
💳 <b>Доступ к клубу «ОСНОВА ПУТИ»</b>

💎 <b>Полный доступ - $33</b>
• Ежедневные ритуалы ЯДРА
• Система отчетности и анализа
• Поддержка сообщества
• Персональная работа с целями
• Доступ к закрытому чату
• Еженедельные вызовы

<b>Способ оплаты:</b> Криптовалюта
• USDT, TON, BTC, ETH и другие
• Быстро, анонимно, без банков
• Автоматическое подтверждение

🎯 <b>Один тариф - максимальная ценность!</b>
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 Получить доступ - $33", callback_data="pay_monthly")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
        ])
        
        await update.callback_query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в handle_payment_options: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def handle_about_club(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка показа информации о клубе."""
    try:
        user = update.effective_user
        telegram_service = TelegramService(context.bot)
        
        # Проверяем, есть ли у пользователя активная подписка
        async with get_db_session() as session:
            from app.services.user_service import UserService
            user_service = UserService(session)
            
            db_user = await user_service.get_user_by_telegram_id(user.id)
            
            if db_user and db_user.is_premium and db_user.subscription_until and db_user.subscription_until > datetime.now():
                # У пользователя есть активная подписка
                await telegram_service.send_about_club_message_for_subscribers(user.id)
            else:
                # У пользователя нет активной подписки
                await telegram_service.send_about_club_message(user.id)
        
    except Exception as e:
        logger.error(f"Ошибка в handle_about_club: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def handle_back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка возврата к стартовому сообщению."""
    try:
        user = update.effective_user
        telegram_service = TelegramService(context.bot)
        
        # Проверяем статус подписки пользователя
        async with get_db_session() as session:
            from app.services.user_service import UserService
            user_service = UserService(session)
            
            db_user = await user_service.get_user_by_telegram_id(user.id)
            
            if db_user and db_user.is_premium and db_user.subscription_until and db_user.subscription_until > datetime.now():
                # У пользователя есть активная подписка - показываем соответствующее сообщение
                username = user.first_name or user.username or str(user.id)
                await telegram_service.send_subscription_active_message(user.id, username, db_user.subscription_until)
            else:
                # У пользователя нет активной подписки - показываем приветственное сообщение
                username = user.first_name or user.username or str(user.id)
                await telegram_service.send_welcome_message(user.id, username)
        
    except Exception as e:
        logger.error(f"Ошибка в handle_back_to_start: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def handle_subscription_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка подтверждения подписки."""
    try:
        # Просто перенаправляем на проверку подписки
        await handle_subscription_check(update, context)
        
    except Exception as e:
        logger.error(f"Ошибка в handle_subscription_confirmed: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def handle_payment_create(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка создания платежа через CryptoBot."""
    try:
        query = update.callback_query
        user = update.effective_user
        callback_data = query.data
        
        # Извлекаем тип тарифа
        tariff_type = callback_data.replace("pay_", "")
        
        # Импортируем сервисы
        from app.services.crypto_service import CryptoService
        
        crypto_service = CryptoService()
        tariff_info = crypto_service.get_tariff_info(tariff_type)
        
        # Создаем счет
        invoice = await crypto_service.create_invoice(
            amount=tariff_info["price"],
            asset=tariff_info["asset"],
            description=tariff_info["description"],
            user_id=user.id
        )
        
        if invoice:
            pay_url = crypto_service.get_payment_url(invoice)
            
            message = f"""
💳 <b>Счет создан!</b>

<b>Тариф:</b> {tariff_info["name"]}
<b>Стоимость:</b> {tariff_info["price"]} {tariff_info["asset"]}
<b>Длительность:</b> {tariff_info["duration_days"]} дней

<b>Способ оплаты:</b> Криптовалюта
• Принимаются: USDT, TON, BTC, ETH и другие
• Быстрая и анонимная оплата  
• Автоматическое подтверждение
• Без банков и карт

<b>Инструкция:</b>
1️⃣ Нажми "Оплатить" (откроется @CryptoBot)
2️⃣ Выбери удобную криптовалюту
3️⃣ Переведи точную сумму
4️⃣ Получи доступ автоматически

⚠️ Счет действителен 24 часа
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Оплатить", url=pay_url)],
                [InlineKeyboardButton("🔄 Проверить оплату", callback_data=f"check_payment_{invoice['invoice_id']}")],
                [InlineKeyboardButton("🔙 Назад", callback_data="payment_options")]
            ])
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
            # Сохраняем информацию о счете в базе данных
            async with get_db_session() as session:
                from app.services.payment_service import PaymentService
                from app.services.user_service import UserService
                
                payment_service = PaymentService(session)
                user_service = UserService(session)
                
                # Получаем пользователя из базы данных по Telegram ID
                db_user = await user_service.get_user_by_telegram_id(user.id)
                if not db_user:
                    logger.error(f"Пользователь с Telegram ID {user.id} не найден в базе данных")
                    await query.edit_message_text(
                        "❌ Ошибка: пользователь не найден. Попробуйте команду /start.",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
                        ])
                    )
                    return
                
                from app.schemas.payment import PaymentCreate
                payment_data = PaymentCreate(
                    user_id=str(db_user.id),  # Используем UUID пользователя из БД
                    amount=float(tariff_info["price"]),
                    currency=tariff_info["asset"],  # Используем asset вместо currency
                    payment_method="cryptobot",
                    tariff_type=tariff_type,
                    external_payment_id=str(invoice['invoice_id'])
                )
                
                await payment_service.create_payment(payment_data)
                logger.info(f"Создан платеж для пользователя {user.id} (UUID: {db_user.id}): {invoice['invoice_id']}")
                
        else:
            await query.edit_message_text(
                "❌ Ошибка создания счета. Попробуйте позже.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data="payment_options")]
                ])
            )
        
    except Exception as e:
        logger.error(f"Ошибка в handle_payment_create: {e}")
        await update.callback_query.answer("❌ Произошла ошибка при создании платежа")


async def handle_payment_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка проверки статуса платежа."""
    try:
        query = update.callback_query
        user = update.effective_user
        callback_data = query.data
        
        # Извлекаем ID счета
        invoice_id = callback_data.replace("check_payment_", "")
        
        # Импортируем сервисы
        from app.services.crypto_service import CryptoService
        
        crypto_service = CryptoService()
        invoice = await crypto_service.get_invoice(invoice_id)
        
        if invoice:
            status = invoice.get("status")
            
            if status == "paid":
                # Платеж выполнен - активируем доступ
                async with get_db_session() as session:
                    from app.services.payment_service import PaymentService
                    from app.services.user_service import UserService
                    
                    payment_service = PaymentService(session)
                    user_service = UserService(session)
                    
                    # Находим платеж
                    payment = await payment_service.get_payment_by_external_id(invoice_id)
                    if payment:
                        # Обновляем статус платежа
                        from app.schemas.payment import PaymentUpdate
                        await payment_service.update_payment(str(payment.id), PaymentUpdate(
                            status="completed",
                            paid_at=invoice.get("paid_at")
                        ))
                        
                        # Активируем подписку пользователя
                        db_user = await user_service.get_user_by_telegram_id(user.id)
                        if db_user:
                            from datetime import datetime, timedelta
                            from app.schemas.user import UserUpdate
                            
                            # Определяем длительность подписки
                            tariff_type = payment.tariff_type or "1month"
                            duration_map = {"1month": 30, "3months": 90, "subscription": 365}
                            duration_days = duration_map.get(tariff_type, 30)
                            
                            subscription_end = datetime.utcnow() + timedelta(days=duration_days)
                            
                            await user_service.update_user(str(db_user.id), UserUpdate(
                                is_premium=True,
                                subscription_end=subscription_end
                            ))
                            
                            logger.info(f"Активирована подписка для пользователя {user.id} до {subscription_end}")
                
                message = """
✅ <b>Оплата подтверждена!</b>

Поздравляем! Ты успешно присоединился к клубу «ОСНОВА ПУТИ».

<b>Что дальше:</b>
📝 Ежедневные отчеты (21:00)
🎯 Еженедельные цели (воскресенье)
💬 Доступ к закрытой группе
📊 Анализ активности

Все функции работают автоматически. Следи за уведомлениями!

<b>Добро пожаловать в ЯДРО!</b>
Начинаем трансформацию уже сегодня 💪
"""
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("💬 Группа клуба", url="https://t.me/+hWoFGCMcaI83YTY0")],
                    [InlineKeyboardButton("ℹ️ О клубе", callback_data="about_club")]
                ])
                
            elif status == "active":
                # Счет создан, но не оплачен
                message = """
⏳ <b>Ожидаем оплату</b>

Счет создан, но оплата еще не поступила.

<b>Что делать:</b>
1️⃣ Убедись, что перевел точную сумму
2️⃣ Подожди несколько минут (до 10 минут)
3️⃣ Проверь еще раз

⚠️ Если прошло больше 10 минут, обратись в поддержку
"""
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Проверить еще раз", callback_data=f"check_payment_{invoice_id}")],
                    [InlineKeyboardButton("💳 Оплатить", url=invoice.get("pay_url", ""))],
                    [InlineKeyboardButton("📞 Поддержка", url="https://t.me/support")]
                ])
                
            else:
                # Другие статусы
                message = f"""
❓ <b>Статус платежа: {status}</b>

Платеж находится в обработке.

Если возникли вопросы, обратитесь в поддержку.
"""
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Проверить еще раз", callback_data=f"check_payment_{invoice_id}")],
                    [InlineKeyboardButton("📞 Поддержка", url="https://t.me/support")]
                ])
                
        else:
            message = """
❌ <b>Ошибка проверки платежа</b>

Не удалось получить информацию о платеже.
Попробуйте позже или обратитесь в поддержку.
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Попробовать еще раз", callback_data=f"check_payment_{invoice_id}")],
                [InlineKeyboardButton("📞 Поддержка", url="https://t.me/support")]
            ])
        
        # Проверяем, изменилось ли содержимое сообщения
        current_text = query.message.text or ""
        current_markup = str(query.message.reply_markup) if query.message.reply_markup else ""
        new_markup_str = str(keyboard)
        
        if current_text != message or current_markup != new_markup_str:
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        else:
            # Содержимое не изменилось
            await query.answer("Статус платежа не изменился")
        
    except Exception as e:
        logger.error(f"Ошибка в handle_payment_check: {e}")
        await update.callback_query.answer("❌ Произошла ошибка при проверке платежа")


