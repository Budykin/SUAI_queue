from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Импорт новых моделей
from .models import User, Subject, Queue


async def get_or_create_user(session: AsyncSession, tg_id: int, full_name: str) -> User:
    """Получить существующего пользователя или создать нового"""
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(tg_id=tg_id, full_name=full_name)
        session.add(user)
        await session.flush()

    return user


async def get_user_by_tg_id(session: AsyncSession, tg_id: int) -> Optional[User]:
    """Получить пользователя по telegram ID"""
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    return result.scalar_one_or_none()


async def ensure_admin_roles(session: AsyncSession, tg_ids: List[int]) -> None:
    """Установить роль admin для указанных пользователей"""
    if not tg_ids:
        return

    result = await session.execute(select(User).where(User.tg_id.in_(tg_ids)))
    users = result.scalars().all()

    for user in users:
        user.role = "admin"


async def list_subjects(session: AsyncSession) -> List[Subject]:
    """Получить список всех предметов"""
    result = await session.execute(select(Subject).order_by(Subject.name))
    return list(result.scalars().all())


async def get_subject(session: AsyncSession, subject_id: int) -> Optional[Subject]:
    """Получить предмет по ID"""
    result = await session.execute(select(Subject).where(Subject.id == subject_id))
    return result.scalar_one_or_none()


async def list_queue_for_subject(session: AsyncSession, subject_id: int) -> List[Queue]:
    """Получить очередь для конкретного предмета"""
    result = await session.execute(
        select(Queue)
        .where(Queue.subject_id == subject_id)
        .order_by(Queue.joined_at)
        .options(selectinload(Queue.user), selectinload(Queue.subject))
    )
    return list(result.scalars().unique().all())


async def is_user_in_queue(session: AsyncSession, user_id: int, subject_id: int) -> bool:
    """Проверить, находится ли пользователь в очереди по предмету"""
    result = await session.execute(
        select(Queue.id).where(
            Queue.user_id == user_id,
            Queue.subject_id == subject_id,
        )
    )
    return result.scalar_one_or_none() is not None


async def add_to_queue(session: AsyncSession, user_id: int, subject_id: int) -> Queue:
    """Добавить пользователя в очередь по предмету"""
    entry = Queue(user_id=user_id, subject_id=subject_id, joined_at=datetime.now())
    session.add(entry)
    await session.flush()
    return entry


async def remove_from_queue(session: AsyncSession, user_id: int, subject_id: int) -> None:
    """Удалить пользователя из очереди по предмету"""
    await session.execute(
        delete(Queue).where(
            Queue.user_id == user_id,
            Queue.subject_id == subject_id,
        )
    )


async def clear_queue(session: AsyncSession, subject_id: int) -> None:
    """Очистить всю очередь по предмету"""
    await session.execute(delete(Queue).where(Queue.subject_id == subject_id))


async def create_subject(session: AsyncSession, name: str) -> Subject:
    """Создать новый предмет"""
    subject = Subject(name=name)
    session.add(subject)
    await session.flush()
    return subject


async def delete_subject(session: AsyncSession, subject_id: int) -> None:
    """Удалить предмет и все связанные записи очереди"""
    # Сначала удаляем все записи очереди для этого предмета
    await session.execute(delete(Queue).where(Queue.subject_id == subject_id))
    # Затем удаляем сам предмет
    await session.execute(delete(Subject).where(Subject.id == subject_id))


async def update_subject(session: AsyncSession, subject_id: int, new_name: str) -> Subject:
    """Обновить название предмета"""
    result = await session.execute(select(Subject).where(Subject.id == subject_id))
    subject = result.scalar_one_or_none()
    if subject:
        subject.name = new_name
        await session.flush()
    return subject