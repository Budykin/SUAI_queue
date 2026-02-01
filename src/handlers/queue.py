from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from src.database import async_session_maker
from src.database.requests import (
    add_to_queue,
    get_subject,
    get_user_by_tg_id,
    is_user_in_queue,
    list_subjects,
    list_queue_for_subject,
    remove_from_queue,
)
# Если ты переименовал файлы клавиатур, проверь импорты здесь:
from src.keyboards.inline import subjects_keyboard, queue_actions_keyboard
from src.keyboards.reply import main_menu_keyboard

router = Router()

@router.message(F.text == "Выбрать дисциплину")
async def choose_discipline(message: Message) -> None:
    async with async_session_maker() as session:
        subjects = await list_subjects(session)
        user = await get_user_by_tg_id(session, message.from_user.id)
        is_admin = user.role == "admin" if user else False

    if not subjects:
        text = (
            "⚠️ <b>Предметы пока не добавлены</b>\n\n"
            "Староста еще не внес дисциплины в систему."
        )
        await message.answer(text, reply_markup=main_menu_keyboard(is_admin=is_admin))
        return

    await message.answer(
        "Выбери дисциплину из списка:",
        reply_markup=subjects_keyboard(subjects),
    )

def _format_queue_text(subject_name: str, entries) -> str:
    if not entries:
        return f"Очередь по предмету <b>{subject_name}</b> пуста."

    lines = [f"Очередь по предмету <b>{subject_name}</b>:"]
    for idx, entry in enumerate(entries, start=1):
        # Используем full_name связанного пользователя
        lines.append(f"{idx}. {entry.user.full_name}")
    return "\n".join(lines)

@router.callback_query(F.data.startswith("subject:"))
async def show_queue(callback: CallbackQuery) -> None:
    subject_id = int(callback.data.split(":")[1])

    async with async_session_maker() as session:
        subject = await get_subject(session, subject_id)
        if not subject:
            await callback.answer("Предмет не найден", show_alert=True)
            return

        entries = await list_queue_for_subject(session, subject_id)
        user = await get_user_by_tg_id(session, callback.from_user.id)

        in_queue = False
        is_admin = False
        if user:
            in_queue = await is_user_in_queue(session, user.tg_id, subject_id)
            is_admin = user.role == "admin"

    text = _format_queue_text(subject.name, entries)
    await callback.message.edit_text(
        text,
        reply_markup=queue_actions_keyboard(
            subject_id=subject_id, # Оставляем аргумент как в клавиатуре
            in_queue=in_queue,
            is_admin=is_admin,
        ),
    )
    await callback.answer()

@router.callback_query(F.data.startswith("queue:join:"))
async def join_queue(callback: CallbackQuery) -> None:
    subject_id = int(callback.data.split(":")[2])

    async with async_session_maker() as session:
        user = await get_user_by_tg_id(session, callback.from_user.id)
        if not user:
            await callback.answer("Сначала нажми /start", show_alert=True)
            return

        if await is_user_in_queue(session, user.tg_id, subject_id):
            await callback.answer("Ты уже в этой очереди!", show_alert=True)
            return

        await add_to_queue(session, user.tg_id, subject_id)
        # Обязательно коммитим изменения
        await session.commit()

        subject = await get_subject(session, subject_id)
        entries = await list_queue_for_subject(session, subject_id)
        is_admin = user.role == "admin"

    text = _format_queue_text(str(subject.name), entries)
    await callback.message.edit_text(
        text,
        reply_markup=queue_actions_keyboard(subject_id, in_queue=True, is_admin=is_admin),
    )
    await callback.answer("Записано!")

@router.callback_query(F.data.startswith("queue:leave:"))
async def leave_queue(callback: CallbackQuery) -> None:
    subject_id = int(callback.data.split(":")[2])

    async with async_session_maker() as session:
        user = await get_user_by_tg_id(session, callback.from_user.id)
        if not user: return

        await remove_from_queue(session, user.tg_id, subject_id)
        await session.commit()

        subject = await get_subject(session, subject_id)
        entries = await list_queue_for_subject(session, subject_id)
        is_admin = user.role == "admin"

    text = _format_queue_text(str(subject.name), entries)
    await callback.message.edit_text(
        text,
        reply_markup=queue_actions_keyboard(subject_id, in_queue=False, is_admin=is_admin),
    )
    await callback.answer("Ты вышел из очереди.")

@router.message(F.text == "Мои очереди")
async def my_queues(message: Message) -> None:
    async with async_session_maker() as session:
        user = await get_user_by_tg_id(session, message.from_user.id)
        if not user:
            await message.answer("Сначала нажми /start.")
            return


        raw_sql = """
            SELECT s.name 
            FROM Queues q
            JOIN Subjects s ON s.id = q.subject_id
            WHERE q.user_id = :user_id
            ORDER BY s.name
        """
        from sqlalchemy import text
        result = await session.execute(text(raw_sql), {"user_id": user.tg_id})
        subject_names = [row[0] for row in result.fetchall()]

    if not subject_names:
        await message.answer("Ты пока не записан ни в одну очередь.",
                             reply_markup=main_menu_keyboard(is_admin=(user.role == "admin")))
        return

    text = "Твои очереди:\n" + "\n".join(f"• {name}" for name in subject_names)
    await message.answer(text, reply_markup=main_menu_keyboard(is_admin=(user.role == "admin")))