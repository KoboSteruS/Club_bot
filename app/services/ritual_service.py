"""
Сервис для управления ритуалами ЯДРА.

Этот модуль содержит логику для:
- Создания и управления ритуалами
- Регистрации пользователей на ритуалы
- Отслеживания ответов пользователей
- Статистики участия
"""

import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from loguru import logger

from app.core.database import AsyncSession
from app.core.exceptions import RitualException
from app.models import (
    Ritual, UserRitual, RitualResponse, User,
    RitualType, RitualSchedule, ResponseType
)
from app.schemas.ritual import (
    RitualCreate, RitualUpdate, UserRitualCreate, 
    RitualResponseCreate, RitualStatsResponse, RitualButtonSchema
)


class RitualService:
    """Сервис для управления ритуалами ЯДРА."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_ritual(self, ritual_data: RitualCreate) -> Ritual:
        """Создать новый ритуал."""
        try:
            # Преобразуем кнопки в JSON
            response_buttons_json = None
            if ritual_data.response_buttons:
                response_buttons_json = json.dumps([
                    button.dict() for button in ritual_data.response_buttons
                ])
            
            ritual = Ritual(
                name=ritual_data.name,
                description=ritual_data.description,
                type=ritual_data.type,
                schedule=ritual_data.schedule,
                send_hour=ritual_data.send_hour,
                send_minute=ritual_data.send_minute,
                weekday=ritual_data.weekday,
                message_title=ritual_data.message_title,
                message_text=ritual_data.message_text,
                response_buttons=response_buttons_json,
                is_active=ritual_data.is_active,
                requires_subscription=ritual_data.requires_subscription,
                sort_order=ritual_data.sort_order
            )
            
            self.session.add(ritual)
            await self.session.commit()
            await self.session.refresh(ritual)
            
            logger.info(f"Создан ритуал: {ritual.name} (ID: {ritual.id})")
            return ritual
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка создания ритуала: {e}")
            raise RitualException(f"Не удалось создать ритуал: {e}")
    
    async def get_ritual_by_id(self, ritual_id: str) -> Optional[Ritual]:
        """Получить ритуал по ID."""
        try:
            stmt = select(Ritual).where(Ritual.id == ritual_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка получения ритуала {ritual_id}: {e}")
            return None
    
    async def get_active_rituals(self, ritual_type: Optional[RitualType] = None) -> List[Ritual]:
        """Получить активные ритуалы."""
        try:
            stmt = select(Ritual).where(Ritual.is_active == True)
            
            if ritual_type:
                stmt = stmt.where(Ritual.type == ritual_type)
            
            stmt = stmt.order_by(Ritual.sort_order.asc(), Ritual.created_at.asc())
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Ошибка получения активных ритуалов: {e}")
            return []
    
    async def register_user_for_ritual(self, user_id: str, ritual_id: str, 
                                     timezone_offset: int = 3) -> UserRitual:
        """Зарегистрировать пользователя на ритуал."""
        try:
            # Проверяем, не зарегистрирован ли уже
            existing_stmt = select(UserRitual).where(
                and_(
                    UserRitual.user_id == user_id,
                    UserRitual.ritual_id == ritual_id
                )
            )
            result = await self.session.execute(existing_stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                logger.info(f"Пользователь {user_id} уже зарегистрирован на ритуал {ritual_id}")
                return existing
            
            # Создаем новую регистрацию
            user_ritual = UserRitual(
                user_id=user_id,
                ritual_id=ritual_id,
                timezone_offset=timezone_offset,
                is_enabled=True
            )
            
            self.session.add(user_ritual)
            await self.session.commit()
            await self.session.refresh(user_ritual)
            
            logger.info(f"Пользователь {user_id} зарегистрирован на ритуал {ritual_id}")
            return user_ritual
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка регистрации пользователя на ритуал: {e}")
            raise RitualException(f"Не удалось зарегистрировать пользователя: {e}")
    
    async def register_user_for_all_rituals(self, user_id: str, timezone_offset: int = 3) -> List[UserRitual]:
        """Зарегистрировать пользователя на все активные ритуалы."""
        try:
            active_rituals = await self.get_active_rituals()
            registrations = []
            
            for ritual in active_rituals:
                registration = await self.register_user_for_ritual(
                    user_id, ritual.id.hex, timezone_offset
                )
                registrations.append(registration)
            
            logger.info(f"Пользователь {user_id} зарегистрирован на {len(registrations)} ритуалов")
            return registrations
            
        except Exception as e:
            logger.error(f"Ошибка массовой регистрации пользователя: {e}")
            raise RitualException(f"Не удалось зарегистрировать пользователя на ритуалы: {e}")
    
    async def get_users_for_ritual_sending(self, ritual_type: RitualType, 
                                         current_time: datetime) -> List[Dict[str, Any]]:
        """Получить пользователей для отправки ритуала."""
        try:
            # Получаем активные ритуалы нужного типа
            rituals_stmt = select(Ritual).where(
                and_(
                    Ritual.type == ritual_type,
                    Ritual.is_active == True
                )
            )
            rituals_result = await self.session.execute(rituals_stmt)
            rituals = rituals_result.scalars().all()
            
            if not rituals:
                logger.debug(f"Нет активных ритуалов типа {ritual_type}")
                return []
            
            users_to_send = []
            
            for ritual in rituals:
                # Получаем пользователей для этого ритуала
                users_stmt = (
                    select(UserRitual, User)
                    .join(User, UserRitual.user_id == User.id)
                    .where(
                        and_(
                            UserRitual.ritual_id == ritual.id.hex,
                            UserRitual.is_enabled == True,
                            User.status == "active"
                        )
                    )
                )
                
                # Добавляем проверку подписки если нужно
                if ritual.requires_subscription:
                    users_stmt = users_stmt.where(User.subscription_until > current_time)
                
                users_result = await self.session.execute(users_stmt)
                user_rituals = users_result.all()
                
                for user_ritual, user in user_rituals:
                    # Проверяем, нужно ли отправлять ритуал сейчас
                    if await self._should_send_ritual(ritual, user_ritual, current_time):
                        users_to_send.append({
                            'user': user,
                            'user_ritual': user_ritual,
                            'ritual': ritual
                        })
            
            logger.info(f"Найдено {len(users_to_send)} пользователей для отправки ритуалов типа {ritual_type}")
            return users_to_send
            
        except Exception as e:
            logger.error(f"Ошибка получения пользователей для ритуала: {e}")
            return []
    
    async def _should_send_ritual(self, ritual: Ritual, user_ritual: UserRitual, 
                                current_time: datetime) -> bool:
        """Проверить, нужно ли отправить ритуал пользователю."""
        try:
            # Учитываем часовой пояс пользователя
            user_time = current_time + timedelta(hours=user_ritual.timezone_offset - 3)  # UTC+3 базовый
            
            # Проверяем время дня
            if user_time.hour != ritual.send_hour or user_time.minute != ritual.send_minute:
                return False
            
            # Проверяем расписание
            if ritual.schedule == RitualSchedule.WEEKLY:
                if ritual.weekday is not None and user_time.weekday() != ritual.weekday:
                    return False
            
            # Проверяем, не отправляли ли уже сегодня/на этой неделе
            if user_ritual.last_sent_at:
                if ritual.schedule == RitualSchedule.DAILY:
                    # Для ежедневных - проверяем, что не отправляли сегодня
                    if user_ritual.last_sent_at.date() == user_time.date():
                        return False
                elif ritual.schedule == RitualSchedule.WEEKLY:
                    # Для еженедельных - проверяем, что не отправляли на этой неделе
                    week_start = user_time - timedelta(days=user_time.weekday())
                    if user_ritual.last_sent_at >= week_start.replace(hour=0, minute=0, second=0):
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки отправки ритуала: {e}")
            return False
    
    async def mark_ritual_sent(self, user_ritual_id: str, sent_at: datetime) -> None:
        """Отметить, что ритуал был отправлен."""
        try:
            stmt = select(UserRitual).where(UserRitual.id == user_ritual_id)
            result = await self.session.execute(stmt)
            user_ritual = result.scalar_one_or_none()
            
            if user_ritual:
                user_ritual.last_sent_at = sent_at
                user_ritual.total_sent += 1
                await self.session.commit()
                
                logger.debug(f"Отмечена отправка ритуала для user_ritual {user_ritual_id}")
            
        except Exception as e:
            logger.error(f"Ошибка отметки отправки ритуала: {e}")
            await self.session.rollback()
    
    async def record_ritual_response(self, response_data: RitualResponseCreate) -> RitualResponse:
        """Записать ответ пользователя на ритуал."""
        try:
            # Создаем запись ответа
            response = RitualResponse(
                user_ritual_id=response_data.user_ritual_id,
                ritual_id=response_data.ritual_id,
                response_type=response_data.response_type,
                response_text=response_data.response_text,
                button_clicked=response_data.button_clicked,
                sent_at=response_data.sent_at,
                responded_at=datetime.now()
            )
            
            self.session.add(response)
            
            # Обновляем статистику UserRitual
            stmt = select(UserRitual).where(UserRitual.id == response_data.user_ritual_id)
            result = await self.session.execute(stmt)
            user_ritual = result.scalar_one_or_none()
            
            if user_ritual:
                user_ritual.total_responses += 1
                if response_data.response_type == ResponseType.COMPLETED:
                    user_ritual.total_completed += 1
                elif response_data.response_type == ResponseType.SKIPPED:
                    user_ritual.total_skipped += 1
            
            await self.session.commit()
            await self.session.refresh(response)
            
            logger.info(f"Записан ответ на ритуал: {response_data.response_type}")
            return response
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка записи ответа на ритуал: {e}")
            raise RitualException(f"Не удалось записать ответ: {e}")
    
    async def get_ritual_stats(self, ritual_id: str) -> Optional[RitualStatsResponse]:
        """Получить статистику ритуала."""
        try:
            # Получаем ритуал
            ritual = await self.get_ritual_by_id(ritual_id)
            if not ritual:
                return None
            
            # Статистика участников
            participants_stmt = select(func.count(UserRitual.id)).where(
                UserRitual.ritual_id == ritual_id
            )
            active_participants_stmt = select(func.count(UserRitual.id)).where(
                and_(
                    UserRitual.ritual_id == ritual_id,
                    UserRitual.is_enabled == True
                )
            )
            
            participants_result = await self.session.execute(participants_stmt)
            active_participants_result = await self.session.execute(active_participants_stmt)
            
            total_participants = participants_result.scalar() or 0
            active_participants = active_participants_result.scalar() or 0
            
            # Статистика отправки и ответов
            totals_stmt = select(
                func.sum(UserRitual.total_sent),
                func.sum(UserRitual.total_responses),
                func.sum(UserRitual.total_completed),
                func.sum(UserRitual.total_skipped),
                func.max(UserRitual.last_sent_at)
            ).where(UserRitual.ritual_id == ritual_id)
            
            totals_result = await self.session.execute(totals_stmt)
            totals = totals_result.first()
            
            total_sent = totals[0] or 0
            total_responses = totals[1] or 0
            total_completed = totals[2] or 0
            total_skipped = totals[3] or 0
            last_sent_at = totals[4]
            
            # Вычисляем проценты
            response_rate = (total_responses / total_sent * 100) if total_sent > 0 else 0
            completion_rate = (total_completed / total_sent * 100) if total_sent > 0 else 0
            
            return RitualStatsResponse(
                ritual_id=ritual_id,
                ritual_name=ritual.name,
                total_participants=total_participants,
                active_participants=active_participants,
                total_sent=total_sent,
                total_responses=total_responses,
                total_completed=total_completed,
                total_skipped=total_skipped,
                response_rate=round(response_rate, 2),
                completion_rate=round(completion_rate, 2),
                last_sent_at=last_sent_at
            )
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики ритуала: {e}")
            return None
    
    async def parse_response_buttons(self, buttons_json: Optional[str]) -> List[RitualButtonSchema]:
        """Парсинг кнопок ответа из JSON."""
        if not buttons_json:
            return []
        
        try:
            buttons_data = json.loads(buttons_json)
            return [RitualButtonSchema(**button) for button in buttons_data]
        except Exception as e:
            logger.error(f"Ошибка парсинга кнопок ритуала: {e}")
            return []
    
    async def create_default_rituals(self) -> List[Ritual]:
        """Создать ритуалы по умолчанию."""
        try:
            default_rituals = [
                # Утренний ритуал
                RitualCreate(
                    name="Утренний ритуал ЯДРА",
                    description="Ежедневное утреннее сообщение для настрой на день",
                    type=RitualType.MORNING,
                    schedule=RitualSchedule.DAILY,
                    send_hour=6,
                    send_minute=30,
                    message_title="🌅 Доброе утро, ЯДРО!",
                    message_text="""🔥 Новый день — новые возможности!

💪 Сегодня ты можешь:
• Сделать больше, чем вчера
• Преодолеть свои ограничения
• Стать сильнее духом

⚡️ Твоя цель сегодня — не просто прожить день, а ВЗЯТЬ от него максимум!

🎯 Что ты выберешь?""",
                    response_buttons=[
                        RitualButtonSchema(
                            text="🔥 Готов к бою!",
                            callback_data="morning_ready",
                            response_type=ResponseType.COMPLETED
                        ),
                        RitualButtonSchema(
                            text="😴 Ещё сплю...",
                            callback_data="morning_sleepy",
                            response_type=ResponseType.SKIPPED
                        )
                    ]
                ),
                
                # Вечерний ритуал
                RitualCreate(
                    name="Вечерний ритуал ЯДРА",
                    description="Ежедневное вечернее подведение итогов",
                    type=RitualType.EVENING,
                    schedule=RitualSchedule.DAILY,
                    send_hour=21,
                    send_minute=0,
                    message_title="🌙 Время подвести итоги дня",
                    message_text="""🎯 Как прошёл твой день?

📊 Время честной оценки:
• Что удалось сделать хорошо?
• Где можно было лучше?
• Что изменишь завтра?

💭 Напиши, что прожил, что понял, где дотянул, где сдался.

⭐️ Каждый день — это урок. Какой урок дал тебе сегодняшний день?""",
                    response_buttons=[
                        RitualButtonSchema(
                            text="📝 Отчёт отправлен",
                            callback_data="evening_reported",
                            response_type=ResponseType.COMPLETED
                        ),
                        RitualButtonSchema(
                            text="🤐 Не готов делиться",
                            callback_data="evening_private",
                            response_type=ResponseType.SKIPPED
                        )
                    ]
                ),
                
                # Еженедельный вызов (понедельник)
                RitualCreate(
                    name="Личный вызов недели",
                    description="Еженедельный вызов для роста",
                    type=RitualType.WEEKLY_CHALLENGE,
                    schedule=RitualSchedule.WEEKLY,
                    weekday=0,  # Понедельник
                    send_hour=9,
                    send_minute=0,
                    message_title="🎯 ВЫЗОВ НЕДЕЛИ",
                    message_text="""💥 Новая неделя — новый уровень!

🏆 Твой личный вызов на эту неделю:

• Выйди из зоны комфорта КАЖДЫЙ день
• Сделай то, что откладывал
• Преодолей один страх
• Научись чему-то новому

🔥 Неделя без вызовов — потерянная неделя!

💪 Принимаешь вызов?""",
                    response_buttons=[
                        RitualButtonSchema(
                            text="💪 Принимаю вызов!",
                            callback_data="challenge_accepted",
                            response_type=ResponseType.COMPLETED
                        ),
                        RitualButtonSchema(
                            text="🤔 Подумаю...",
                            callback_data="challenge_maybe",
                            response_type=ResponseType.PARTIAL
                        )
                    ]
                ),
                
                # Цели на неделю (воскресенье)
                RitualCreate(
                    name="Цели на неделю",
                    description="Планирование целей на предстоящую неделю",
                    type=RitualType.WEEKLY_GOALS,
                    schedule=RitualSchedule.WEEKLY,
                    weekday=6,  # Воскресенье
                    send_hour=18,
                    send_minute=0,
                    message_title="🎯 Фиксация недели",
                    message_text="""📋 Время планировать новую неделю!

🎯 Поставь цели на следующие 7 дней:

• 3 главные задачи
• 1 большая цель
• 1 навык для развития
• 1 привычка для внедрения

💡 Помни: цель без плана — это просто мечта!

✍️ Запиши свои цели и план их достижения.""",
                    response_buttons=[
                        RitualButtonSchema(
                            text="✅ Цели установлены",
                            callback_data="goals_set",
                            response_type=ResponseType.COMPLETED
                        ),
                        RitualButtonSchema(
                            text="📝 Ещё планирую",
                            callback_data="goals_planning",
                            response_type=ResponseType.PARTIAL
                        )
                    ]
                ),
                
                # Пятничный цикл
                RitualCreate(
                    name="Пятничный ритуал",
                    description="Циклический ритуал подведения итогов недели",
                    type=RitualType.FRIDAY_CYCLE,
                    schedule=RitualSchedule.WEEKLY,
                    weekday=4,  # Пятница
                    send_hour=17,
                    send_minute=0,
                    message_title="🏁 Финиш недели!",
                    message_text="""🎉 Ещё одна неделя позади!

📊 Время анализа:
• Какие победы у тебя на этой неделе?
• Что не получилось и почему?
• Какие уроки извлёк?
• Как будешь действовать по-другому?

🔄 Каждая неделя — это итерация твоего роста.

💪 Готов к новому циклу развития?""",
                    response_buttons=[
                        RitualButtonSchema(
                            text="🏆 Неделя зачётная!",
                            callback_data="week_successful",
                            response_type=ResponseType.COMPLETED
                        ),
                        RitualButtonSchema(
                            text="📈 Есть над чем работать",
                            callback_data="week_improving",
                            response_type=ResponseType.PARTIAL
                        )
                    ]
                )
            ]
            
            created_rituals = []
            for ritual_data in default_rituals:
                # Проверяем, не существует ли уже ритуал с таким именем
                existing_stmt = select(Ritual).where(Ritual.name == ritual_data.name)
                result = await self.session.execute(existing_stmt)
                existing = result.scalar_one_or_none()
                
                if not existing:
                    ritual = await self.create_ritual(ritual_data)
                    created_rituals.append(ritual)
                else:
                    logger.info(f"Ритуал '{ritual_data.name}' уже существует")
                    created_rituals.append(existing)
            
            logger.info(f"Создано/найдено {len(created_rituals)} ритуалов по умолчанию")
            return created_rituals
            
        except Exception as e:
            logger.error(f"Ошибка создания ритуалов по умолчанию: {e}")
            raise RitualException(f"Не удалось создать ритуалы по умолчанию: {e}")

