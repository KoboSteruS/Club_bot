"""
Административные инструменты для управления пользователями.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Добавляем корневую папку в путь
sys.path.append(str(Path(__file__).parent))

from app.core.database import get_db_session
from app.services.user_service import UserService
from app.schemas.user import UserUpdate


async def set_user_subscription(telegram_id: int, days: int = 30):
    """Установка подписки пользователю."""
    async with get_db_session() as session:
        user_service = UserService(session)
        
        # Ищем пользователя
        user = await user_service.get_user_by_telegram_id(telegram_id)
        
        if not user:
            print(f"❌ Пользователь с telegram_id {telegram_id} не найден в базе данных")
            return
        
        # Устанавливаем подписку
        subscription_until = datetime.now() + timedelta(days=days)
        
        await user_service.update_user(str(user.id), UserUpdate(
            subscription_until=subscription_until,
            is_premium=True,
            status="active"
        ))
        
        print(f"✅ Установлена подписка для пользователя {telegram_id}")
        print(f"  Подписка до: {subscription_until.strftime('%d.%m.%Y %H:%M')}")
        print(f"  Дней: {days}")
        print(f"  Premium: True")
        print(f"  Статус: active")


async def remove_user_subscription(telegram_id: int):
    """Удаление подписки пользователя."""
    async with get_db_session() as session:
        user_service = UserService(session)
        
        # Ищем пользователя
        user = await user_service.get_user_by_telegram_id(telegram_id)
        
        if not user:
            print(f"❌ Пользователь с telegram_id {telegram_id} не найден в базе данных")
            return
        
        # Удаляем подписку
        await user_service.update_user(str(user.id), UserUpdate(
            subscription_until=None,
            is_premium=False,
            status="pending"
        ))
        
        print(f"✅ Удалена подписка для пользователя {telegram_id}")


async def check_user_status(telegram_id: int):
    """Проверка статуса пользователя."""
    async with get_db_session() as session:
        user_service = UserService(session)
        
        # Ищем пользователя
        user = await user_service.get_user_by_telegram_id(telegram_id)
        
        if not user:
            print(f"❌ Пользователь с telegram_id {telegram_id} не найден в базе данных")
            return
        
        print(f"✅ Пользователь найден:")
        print(f"  ID: {user.id}")
        print(f"  Telegram ID: {user.telegram_id}")
        print(f"  Username: @{user.username}")
        print(f"  Имя: {user.first_name} {user.last_name}")
        print(f"  Статус: {user.status}")
        print(f"  В группе: {user.is_in_group}")
        print(f"  Подписан на канал: {user.is_subscribed_to_channel}")
        print(f"  Premium: {user.is_premium}")
        print(f"  Подписка до: {user.subscription_until}")
        print(f"  Создан: {user.created_at}")
        print(f"  Обновлен: {user.updated_at}")
        
        # Проверяем активность подписки
        if user.subscription_until:
            if user.subscription_until > datetime.now():
                print(f"✅ Активная подписка до {user.subscription_until}")
            else:
                print(f"❌ Подписка истекла {user.subscription_until}")
        else:
            print("❌ Нет активной подписки")


async def main():
    """Основная функция."""
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python admin_tools.py set <telegram_id> [days]")
        print("  python admin_tools.py remove <telegram_id>")
        print("  python admin_tools.py check <telegram_id>")
        print("Примеры:")
        print("  python admin_tools.py set 1670311707")
        print("  python admin_tools.py set 1670311707 7")
        print("  python admin_tools.py remove 1670311707")
        print("  python admin_tools.py check 1670311707")
        return
    
    command = sys.argv[1]
    
    if command == "set":
        if len(sys.argv) < 3:
            print("❌ Ошибка: укажите telegram_id")
            return
        
        try:
            telegram_id = int(sys.argv[2])
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            await set_user_subscription(telegram_id, days)
        except ValueError:
            print("❌ Ошибка: telegram_id и days должны быть числами")
    
    elif command == "remove":
        if len(sys.argv) < 3:
            print("❌ Ошибка: укажите telegram_id")
            return
        
        try:
            telegram_id = int(sys.argv[2])
            await remove_user_subscription(telegram_id)
        except ValueError:
            print("❌ Ошибка: telegram_id должен быть числом")
    
    elif command == "check":
        if len(sys.argv) < 3:
            print("❌ Ошибка: укажите telegram_id")
            return
        
        try:
            telegram_id = int(sys.argv[2])
            await check_user_status(telegram_id)
        except ValueError:
            print("❌ Ошибка: telegram_id должен быть числом")
    
    else:
        print("❌ Ошибка: неизвестная команда. Используйте 'set', 'remove' или 'check'")


if __name__ == "__main__":
    asyncio.run(main())

