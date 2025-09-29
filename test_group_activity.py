#!/usr/bin/env python3
"""
Скрипт для проверки активности в группе.

Проверяет:
1. Настройки бота и группы
2. Права бота в группе
3. Активность пользователей в группе
4. Статистику из базы данных
"""

import asyncio
import sys
from datetime import datetime, date
from loguru import logger

# Добавляем путь к проекту
sys.path.append('.')

from config.settings import get_settings
from app.core.database import get_db_session, init_database
from app.services import ActivityService, UserService
from app.services.telegram_service import TelegramService
from telegram import Bot


async def check_bot_group_settings():
    """Проверка настроек бота и группы."""
    logger.info("🔍 Проверяем настройки бота и группы...")
    
    settings = get_settings()
    
    print(f"📱 BOT_TOKEN: {settings.BOT_TOKEN[:10]}...")
    print(f"🏢 GROUP_ID: {settings.GROUP_ID}")
    print(f"📺 CHANNEL_ID: {settings.CHANNEL_ID}")
    print(f"👑 ADMIN_IDS: {settings.ADMIN_IDS}")
    
    return settings


async def check_bot_permissions():
    """Проверка прав бота в группе."""
    logger.info("🔐 Проверяем права бота в группе...")
    
    settings = get_settings()
    bot = Bot(token=settings.BOT_TOKEN)
    
    try:
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        print(f"🤖 Бот: @{bot_info.username} ({bot_info.first_name})")
        
        # Получаем информацию о группе
        if settings.GROUP_ID:
            try:
                chat_info = await bot.get_chat(int(settings.GROUP_ID))
                print(f"🏢 Группа: {chat_info.title}")
                print(f"📝 Тип чата: {chat_info.type}")
                
                # Проверяем права бота в группе
                bot_member = await bot.get_chat_member(int(settings.GROUP_ID), bot_info.id)
                print(f"🔐 Статус бота в группе: {bot_member.status}")
                print(f"✅ Может читать сообщения: {bot_member.can_read_all_group_messages}")
                print(f"✅ Может удалять сообщения: {bot_member.can_delete_messages}")
                
                return True
                
            except Exception as e:
                print(f"❌ Ошибка получения информации о группе: {e}")
                return False
        else:
            print("❌ GROUP_ID не настроен")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка получения информации о боте: {e}")
        return False


async def check_activity_in_database():
    """Проверка активности в базе данных."""
    logger.info("📊 Проверяем активность в базе данных...")
    
    try:
        async with get_db_session() as session:
            activity_service = ActivityService(session)
            user_service = UserService(session)
            
            # Проверяем общую статистику
            today = date.today()
            yesterday = date.fromordinal(today.toordinal() - 1)
            
            print(f"\n📅 Статистика активности:")
            print(f"   Сегодня ({today}):")
            
            # Получаем статистику активности
            today_stats = await activity_service.get_activity_stats_for_date(today)
            yesterday_stats = await activity_service.get_activity_stats_for_date(yesterday)
            
            print(f"   • Сообщений: {today_stats.get('messages', 0)}")
            print(f"   • Активных пользователей: {today_stats.get('active_users', 0)}")
            
            print(f"   Вчера ({yesterday}):")
            print(f"   • Сообщений: {yesterday_stats.get('messages', 0)}")
            print(f"   • Активных пользователей: {yesterday_stats.get('active_users', 0)}")
            
            # Проверяем участников группы
            group_members = await user_service.get_users_by_status("active")
            group_members_count = len([u for u in group_members if u.is_in_group])
            
            print(f"\n👥 Участники группы:")
            print(f"   • Всего пользователей: {len(group_members)}")
            print(f"   • В группе: {group_members_count}")
            
            # Показываем последние активности
            print(f"\n📝 Последние активности:")
            # Здесь нужно добавить метод для получения последних активностей
            
    except Exception as e:
        logger.error(f"Ошибка проверки активности в БД: {e}")


async def test_message_handling():
    """Тестирование обработки сообщений."""
    logger.info("🧪 Тестируем обработку сообщений...")
    
    settings = get_settings()
    bot = Bot(token=settings.BOT_TOKEN)
    telegram_service = TelegramService(bot)
    
    try:
        # Проверяем, может ли бот получать обновления
        updates = await bot.get_updates(limit=10)
        print(f"📨 Получено обновлений: {len(updates)}")
        
        for update in updates[-5:]:  # Показываем последние 5
            if update.message:
                chat_id = update.message.chat.id
                chat_type = update.message.chat.type
                from_user = update.message.from_user.username if update.message.from_user else "Unknown"
                
                print(f"   • Чат {chat_id} ({chat_type}): @{from_user}")
                
                # Проверяем, из нашей ли это группы
                if str(chat_id) == settings.GROUP_ID:
                    print(f"     ✅ Это наша группа!")
                else:
                    print(f"     ❌ Это не наша группа")
                    
    except Exception as e:
        logger.error(f"Ошибка тестирования сообщений: {e}")


async def main():
    """Основная функция."""
    print("🚀 Проверка активности в группе")
    print("=" * 50)
    
    # Инициализируем базу данных
    await init_database()
    
    # Проверяем настройки
    settings = await check_bot_group_settings()
    
    print("\n" + "=" * 50)
    
    # Проверяем права бота
    bot_ok = await check_bot_permissions()
    
    print("\n" + "=" * 50)
    
    # Проверяем активность в БД
    await check_activity_in_database()
    
    print("\n" + "=" * 50)
    
    # Тестируем обработку сообщений
    await test_message_handling()
    
    print("\n" + "=" * 50)
    print("✅ Проверка завершена")
    
    if not bot_ok:
        print("❌ Проблемы с настройками бота или группы!")
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(main())
