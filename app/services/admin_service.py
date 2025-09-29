"""
Сервис для управления администраторами.
"""

import os
import tempfile
from typing import List, Dict, Any
from loguru import logger

from config.settings import get_settings


class AdminService:
    """Сервис для управления администраторами."""
    
    def __init__(self):
        """Инициализация сервиса."""
        self.env_file_path = ".env"
    
    def _reload_settings(self):
        """Перезагружает настройки из .env файла."""
        # Импортируем модуль заново для перезагрузки настроек
        import importlib
        import config.settings
        importlib.reload(config.settings)
        return config.settings.get_settings()
    
    async def get_current_admins(self) -> List[Dict[str, Any]]:
        """
        Получить список текущих администраторов.
        
        Returns:
            List[Dict[str, Any]]: Список администраторов с их данными
        """
        try:
            settings = self._reload_settings()
            admin_ids = settings.admin_ids_list
            
            # Здесь можно добавить получение дополнительной информации о админах
            # из базы данных или Telegram API
            admins = []
            for admin_id in admin_ids:
                is_super_admin = admin_id == settings.SUPER_ADMIN_ID
                admins.append({
                    "id": admin_id,
                    "is_super_admin": is_super_admin,
                    "username": f"admin_{admin_id}"  # Можно получить из базы или API
                })
            
            return admins
            
        except Exception as e:
            logger.error(f"Ошибка получения списка администраторов: {e}")
            return []
    
    async def add_admin(self, admin_id: int, current_admin_id: int) -> Dict[str, Any]:
        """
        Добавить нового администратора.
        
        Args:
            admin_id: ID нового администратора
            current_admin_id: ID текущего администратора (для проверки прав)
            
        Returns:
            Dict[str, Any]: Результат операции
        """
        try:
            # Получаем актуальные настройки
            settings = self._reload_settings()
            
            # Проверяем права текущего администратора
            if current_admin_id != settings.SUPER_ADMIN_ID:
                return {
                    "success": False,
                    "message": "❌ Только супер-администратор может добавлять новых администраторов."
                }
            
            # Проверяем, не является ли уже администратором
            current_admins = settings.admin_ids_list
            if admin_id in current_admins:
                return {
                    "success": False,
                    "message": f"❌ Пользователь с ID {admin_id} уже является администратором."
                }
            
            # Читаем текущий .env файл
            if not os.path.exists(self.env_file_path):
                return {
                    "success": False,
                    "message": "❌ Файл настроек не найден."
                }
            
            with open(self.env_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Обновляем строку с ADMIN_IDS
            updated = False
            new_lines = []
            for line in lines:
                if line.startswith('ADMIN_IDS='):
                    # Добавляем нового админа к существующим
                    current_ids = line.split('=', 1)[1].strip()
                    if current_ids:
                        new_ids = f"{current_ids},{admin_id}"
                    else:
                        new_ids = str(admin_id)
                    new_lines.append(f'ADMIN_IDS={new_ids}\n')
                    updated = True
                else:
                    new_lines.append(line)
            
            if not updated:
                # Если строка ADMIN_IDS не найдена, добавляем её
                new_lines.append(f'ADMIN_IDS={admin_id}\n')
            
            # Записываем обновленный файл
            with open(self.env_file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            logger.info(f"Добавлен новый администратор: {admin_id}")
            
            return {
                "success": True,
                "message": f"✅ Пользователь с ID {admin_id} успешно добавлен в администраторы."
            }
            
        except Exception as e:
            logger.error(f"Ошибка добавления администратора: {e}")
            return {
                "success": False,
                "message": f"❌ Произошла ошибка при добавлении администратора: {str(e)}"
            }
    
    async def remove_admin(self, admin_id: int, current_admin_id: int) -> Dict[str, Any]:
        """
        Удалить администратора.
        
        Args:
            admin_id: ID администратора для удаления
            current_admin_id: ID текущего администратора (для проверки прав)
            
        Returns:
            Dict[str, Any]: Результат операции
        """
        try:
            # Получаем актуальные настройки
            settings = self._reload_settings()
            
            # Проверяем права текущего администратора
            if current_admin_id != settings.SUPER_ADMIN_ID:
                return {
                    "success": False,
                    "message": "❌ Только супер-администратор может удалять администраторов."
                }
            
            # Проверяем, что не удаляем супер-администратора
            if admin_id == settings.SUPER_ADMIN_ID:
                return {
                    "success": False,
                    "message": "❌ Нельзя удалить супер-администратора."
                }
            
            # Проверяем, является ли администратором
            current_admins = settings.admin_ids_list
            if admin_id not in current_admins:
                return {
                    "success": False,
                    "message": f"❌ Пользователь с ID {admin_id} не является администратором."
                }
            
            # Читаем текущий .env файл
            if not os.path.exists(self.env_file_path):
                return {
                    "success": False,
                    "message": "❌ Файл настроек не найден."
                }
            
            with open(self.env_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Обновляем строку с ADMIN_IDS
            updated = False
            new_lines = []
            for line in lines:
                if line.startswith('ADMIN_IDS='):
                    # Удаляем админа из списка
                    current_ids = line.split('=', 1)[1].strip()
                    if current_ids:
                        admin_list = [x.strip() for x in current_ids.split(',') if x.strip()]
                        if str(admin_id) in admin_list:
                            admin_list.remove(str(admin_id))
                            new_ids = ','.join(admin_list) if admin_list else ''
                            new_lines.append(f'ADMIN_IDS={new_ids}\n')
                            updated = True
                        else:
                            new_lines.append(line)
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            
            # Записываем обновленный файл
            with open(self.env_file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            logger.info(f"Удален администратор: {admin_id}")
            
            return {
                "success": True,
                "message": f"✅ Пользователь с ID {admin_id} успешно удален из администраторов."
            }
            
        except Exception as e:
            logger.error(f"Ошибка удаления администратора: {e}")
            return {
                "success": False,
                "message": f"❌ Произошла ошибка при удалении администратора: {str(e)}"
            }
    
    async def get_admin_info(self, admin_id: int) -> Dict[str, Any]:
        """
        Получить информацию об администраторе.
        
        Args:
            admin_id: ID администратора
            
        Returns:
            Dict[str, Any]: Информация об администраторе
        """
        try:
            current_admins = self.settings.admin_ids_list
            is_admin = admin_id in current_admins
            is_super_admin = admin_id == self.settings.SUPER_ADMIN_ID
            
            return {
                "id": admin_id,
                "is_admin": is_admin,
                "is_super_admin": is_super_admin,
                "can_manage_admins": is_super_admin
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения информации об администраторе: {e}")
            return {
                "id": admin_id,
                "is_admin": False,
                "is_super_admin": False,
                "can_manage_admins": False
            }
