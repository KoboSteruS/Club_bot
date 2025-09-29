#!/usr/bin/env python3
"""
Скрипт для тестирования обработки сообщений в группе.

Проверяет, получает ли бот сообщения из группы.
"""

import asyncio
import sys
from datetime import datetime
from loguru import logger

# Добавляем путь к проекту
sys.path.append('.')

from config.settings import get_settings
from telegram import Bot


async def test_group_messages():
    """Тестирование получения сообщений из группы."""
    logger.info("🧪 Тестируем получение сообщений из группы...")
    
    settings = get_settings()
    bot = Bot(token=settings.BOT_TOKEN)
    
    try:
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        print(f"🤖 Бот: @{bot_info.username}")
        
        # Получаем информацию о группе
        if settings.GROUP_ID:
            chat_info = await bot.get_chat(int(settings.GROUP_ID))
            print(f"🏢 Группа: {chat_info.title}")
            
            # Получаем последние обновления
            updates = await bot.get_updates(limit=20)
            print(f"📨 Получено обновлений: {len(updates)}")
            
            group_updates = []
            for update in updates:
                if update.message and str(update.message.chat.id) == settings.GROUP_ID:
                    group_updates.append(update)
            
            print(f"📝 Сообщений из группы: {len(group_updates)}")
            
            # Показываем последние сообщения из группы
            for update in group_updates[-5:]:
                message = update.message
                user = message.from_user
                timestamp = datetime.fromtimestamp(message.date)
                
                print(f"   • {timestamp.strftime('%H:%M:%S')} - @{user.username}: {message.text[:50] if message.text else 'медиа'}")
            
            # Проверяем права бота
            bot_member = await bot.get_chat_member(int(settings.GROUP_ID), bot_info.id)
            print(f"🔐 Статус бота: {bot_member.status}")
            
            if hasattr(bot_member, 'can_read_all_group_messages'):
                print(f"📖 Может читать все сообщения: {bot_member.can_read_all_group_messages}")
            else:
                print("📖 Права на чтение сообщений: не определены (возможно, админ)")
            
            return len(group_updates) > 0
            
        else:
            print("❌ GROUP_ID не настроен")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка тестирования: {e}")
        return False


async def main():
    """Основная функция."""
    print("🧪 Тест получения сообщений из группы")
    print("=" * 50)
    
    success = await test_group_messages()
    
    print("=" * 50)
    if success:
        print("✅ Бот получает сообщения из группы")
    else:
        print("❌ Бот НЕ получает сообщения из группы")
        print("\nВозможные причины:")
        print("1. Бот не добавлен в группу")
        print("2. У бота нет прав на чтение сообщений")
        print("3. Группа настроена неправильно")
        print("4. Webhook настроен вместо polling")
    
    return success


if __name__ == "__main__":
    asyncio.run(main())
