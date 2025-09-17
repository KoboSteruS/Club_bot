"""
Основной обработчик для ClubBot согласно ТЗ.

Обрабатывает основные callback'ы: проверка подписки, оплата, информация о клубе.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger

from app.core.database import get_db_session
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
            
        await query.answer()
        
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
        if update.callback_query:
            await update.callback_query.answer("❌ Произошла ошибка")


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
            
            message = """
✅ <b>Подписка подтверждена!</b>

Отлично! Ты подписан на основной канал.

Теперь для полного доступа к клубу необходимо оплатить участие.

<b>Что даст оплаченное участие:</b>
🧘 Ежедневные ритуалы ЯДРА
📝 Система отчетности (21:00)
🎯 Еженедельные цели
💬 Доступ к закрытой группе
📊 Анализ активности

Готов оплатить доступ?
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Оплатить доступ", callback_data="payment_options")],
                [InlineKeyboardButton("📘 Узнать больше", callback_data="about_club")]
            ])
            
        else:
            # Пользователь не подписан
            message = """
❌ <b>Подписка не найдена</b>

Для доступа к клубу необходимо подписаться на основной канал:
@osnovaputi

<b>Что нужно сделать:</b>
1️⃣ Нажми кнопку "Подписаться"
2️⃣ Подпишись на канал
3️⃣ Вернись сюда и нажми "Проверить снова"

<b>Что вас ждет в канале:</b>
• Дисциплина. Энергия. Движение
• Без воды. Без гуру. Без масок
• Только ты, реальность и направление
• Анонсы и обновления клуба
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Подписаться", url="https://t.me/osnovaputi")],
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
💳 <b>Выбор тарифа участия</b>

🧪 <b>ТЕСТОВЫЙ РЕЖИМ - Копеечные цены!</b>

💎 <b>1 месяц - 0.1 USDT</b> (ТЕСТ)
• Полный доступ к клубу на месяц
• Ежедневные ритуалы ЯДРА
• Система отчетности
• Поддержка сообщества

💎 <b>3 месяца - 0.2 USDT</b> (ТЕСТ)
• Все возможности 1 месяца
• Более глубокое погружение
• Формирование устойчивых привычек

💎 <b>Подписка - 0.5 USDT</b> (ТЕСТ)
• Безлимитный доступ
• Максимальный результат
• Полная трансформация

<b>Способ оплаты:</b> Криптовалюта
• USDT, TON, BTC, ETH и другие
• Быстро, анонимно, без банков
• Автоматическое подтверждение

⚡ Тестовые цены для отладки!
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 1 месяц - 0.1 USDT", callback_data="pay_1month")],
            [InlineKeyboardButton("💎 3 месяца - 0.2 USDT", callback_data="pay_3months")],
            [InlineKeyboardButton("💎 Подписка - 0.5 USDT", callback_data="pay_subscription")],
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
        
        await telegram_service.send_about_club_message(user.id)
        
    except Exception as e:
        logger.error(f"Ошибка в handle_about_club: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def handle_back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка возврата к стартовому сообщению."""
    try:
        user = update.effective_user
        telegram_service = TelegramService(context.bot)
        
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
                payment_service = PaymentService(session)
                
                from app.schemas.payment import PaymentCreate
                payment_data = PaymentCreate(
                    user_id=str(user.id),  # Конвертируем в строку
                    amount=float(tariff_info["price"]),
                    currency=tariff_info["asset"],  # Используем asset вместо currency
                    payment_method="cryptobot",
                    tariff_type=tariff_type,
                    external_payment_id=str(invoice['invoice_id'])
                )
                
                await payment_service.create_payment(payment_data)
                logger.info(f"Создан платеж для пользователя {user.id}: {invoice['invoice_id']}")
                
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
🧘 Ежедневные ритуалы ЯДРА в 6:30 и 21:00
📝 Отчеты о дне в 21:00
🎯 Еженедельные цели в воскресенье
💬 Доступ к закрытой группе
📊 Анализ твоей активности

<b>Добро пожаловать в ЯДРО!</b>
Начинаем трансформацию уже сегодня 💪
"""
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚀 Начать путь", callback_data="start_journey")],
                    [InlineKeyboardButton("💬 Группа клуба", url="https://t.me/osnovaputi_club")]
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
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в handle_payment_check: {e}")
        await update.callback_query.answer("❌ Произошла ошибка при проверке платежа")
