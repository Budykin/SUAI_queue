from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from src.database import async_session_maker
from src.database.requests import (
    clear_queue,
    create_subject,
    delete_subject,
    get_subject,
    get_user_by_tg_id,
    list_subjects,
    update_subject,
)
from src.keyboards.inline import (
    admin_subjects_keyboard,
    confirm_delete_subject_keyboard,
    queue_actions_keyboard,
    queue_clear_confirmation_keyboard,
)
from src.keyboards.reply import main_menu_keyboard


router = Router()


class AddsubjectStates(StatesGroup):
    waiting_for_name = State()


class EditsubjectStates(StatesGroup):
    waiting_for_name = State()

@router.callback_query(F.data.startswith("queue:clear1:"))
async def clear_queue_confirmation(callback: CallbackQuery) -> None:
    subject_id = int(callback.data.split(":")[2])
    text = "⚙️ Подтвердите удаление:"
    await callback.message.edit_text(text, reply_markup=queue_clear_confirmation_keyboard(subject_id))


@router.callback_query(F.data.startswith("queue:clear2:"))
async def clear_queue_handler(callback: CallbackQuery) -> None:
    subject_id = int(callback.data.split(":")[2])

    async with async_session_maker() as session:
        user = await get_user_by_tg_id(session, callback.from_user.id)
        if not user or user.role != "admin":
            await callback.answer("Эта функция доступна только старостам.", show_alert=True)
            return

        subject = await get_subject(session, subject_id)
        if not subject:
            await callback.answer("Дисциплина не найдена.", show_alert=True)
            return

        await clear_queue(session, subject_id)
        await session.commit()

    text = f"Очередь по дисциплине <b>{subject.name}</b> очищена."
    await callback.message.edit_text(
        text,
        reply_markup=queue_actions_keyboard(
            subject_id=subject_id,
            in_queue=False,
            is_admin=True,
        ),
    )
    await callback.answer("Очередь очищена.")


@router.message(F.text == "⚙️ Управление дисциплинами")
async def manage_subjects(message: Message) -> None:
    """Показывает список дисциплин для управления (только для админов)"""
    async with async_session_maker() as session:
        user = await get_user_by_tg_id(session, message.from_user.id)
        if not user or user.role != "admin":
            await message.answer("Эта функция доступна только старостам.")
            return

        subjects = await list_subjects(session)

    if not subjects:
        text = "Нет дисциплин в базе. Нажми '➕ Добавить дисциплину', чтобы создать первую."
        await message.answer(
            text,
            reply_markup=admin_subjects_keyboard(subjects),
        )
        return

    text = "📚 <b>Управление дисциплинами</b>\n\nВыбери дисциплину для удаления или добавь новую:"
    await message.answer(
        text,
        reply_markup=admin_subjects_keyboard(subjects),
    )


@router.callback_query(F.data == "admin:subjects_back")
async def subjects_back(callback: CallbackQuery) -> None:
    """Возврат к главному меню из управления дисциплинами"""
    async with async_session_maker() as session:
        user = await get_user_by_tg_id(session, callback.from_user.id)
        if not user or user.role != "admin":
            await callback.answer("Эта функция доступна только старостам.", show_alert=True)
            return
        is_admin = user.role == "admin"

    text = "Главное меню"
    await callback.message.answer(text, reply_markup=main_menu_keyboard(is_admin=is_admin))
    await callback.answer()


@router.callback_query(F.data == "admin:add_disc")
async def add_subject_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало процесса добавления дисциплины"""
    async with async_session_maker() as session:
        user = await get_user_by_tg_id(session, callback.from_user.id)
        if not user or user.role != "admin":
            await callback.answer("Эта функция доступна только старостам.", show_alert=True)
            return

    await callback.message.edit_text("Введи название новой дисциплины:")
    await state.set_state(AddsubjectStates.waiting_for_name)
    await callback.answer()


@router.message(AddsubjectStates.waiting_for_name)
async def add_subject_process(message: Message, state: FSMContext) -> None:
    """Обработка ввода названия дисциплины"""
    async with async_session_maker() as session:
        user = await get_user_by_tg_id(session, message.from_user.id)
        if not user or user.role != "admin":
            await message.answer("Эта функция доступна только старостам.")
            await state.clear()
            return

        subject_name = message.text.strip()
        if not subject_name or len(subject_name) > 100:
            await message.answer("Название дисциплины должно быть от 1 до 100 символов. Попробуй ещё раз:")
            return

        # Проверяем, нет ли уже такой дисциплины
        existing = await list_subjects(session)
        if any(d.name.lower() == subject_name.lower() for d in existing):
            await message.answer(f"Дисциплина '{subject_name}' уже существует. Введи другое название:")
            return

        await create_subject(session, subject_name)
        await session.commit()

        subjects = await list_subjects(session)

    text = f"✅ Дисциплина '<b>{subject_name}</b>' успешно добавлена!\n\n📚 <b>Управление дисциплинами</b>"
    await message.answer(
        text,
        reply_markup=admin_subjects_keyboard(subjects),
    )
    await state.clear()


@router.callback_query(F.data.startswith("admin:delete_disc:"))
async def delete_subject_confirm(callback: CallbackQuery) -> None:
    """Запрос подтверждения удаления дисциплины"""
    async with async_session_maker() as session:
        user = await get_user_by_tg_id(session, callback.from_user.id)
        if not user or user.role != "admin":
            await callback.answer("Эта функция доступна только старостам.", show_alert=True)
            return

        subject_id = int(callback.data.split(":")[2])
        subject = await get_subject(session, subject_id)
        if not subject:
            await callback.answer("Дисциплина не найдена.", show_alert=True)
            return

    text = (
        f"⚠️ <b>Подтверждение удаления</b>\n\n"
        f"Ты уверен, что хочешь удалить дисциплину '<b>{subject.name}</b>'?\n\n"
        f"Это действие удалит дисциплину и <b>все записи очереди</b> по ней. Отменить это действие будет невозможно."
    )
    await callback.message.edit_text(
        text,
        reply_markup=confirm_delete_subject_keyboard(subject_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:confirm_delete:"))
async def delete_subject_process(callback: CallbackQuery) -> None:
    """Удаление дисциплины после подтверждения"""
    async with async_session_maker() as session:
        user = await get_user_by_tg_id(session, callback.from_user.id)
        if not user or user.role != "admin":
            await callback.answer("Эта функция доступна только старостам.", show_alert=True)
            return

        subject_id = int(callback.data.split(":")[2])
        subject = await get_subject(session, subject_id)
        if not subject:
            await callback.answer("Дисциплина не найдена.", show_alert=True)
            return

        subject_name = subject.name
        await delete_subject(session, subject_id)
        await session.commit()

        subjects = await list_subjects(session)

    text = f"✅ Дисциплина '<b>{subject_name}</b>' и все связанные очереди удалены.\n\n📚 <b>Управление дисциплинами</b>"
    await callback.message.edit_text(
        text,
        reply_markup=admin_subjects_keyboard(subjects),
    )
    await callback.answer("Дисциплина удалена.")


@router.callback_query(F.data.startswith("admin:edit_disc:"))
async def edit_subject_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало процесса редактирования дисциплины"""
    async with async_session_maker() as session:
        user = await get_user_by_tg_id(session, callback.from_user.id)
        if not user or user.role != "admin":
            await callback.answer("Эта функция доступна только старостам.", show_alert=True)
            return

        subject_id = int(callback.data.split(":")[2])
        subject = await get_subject(session, subject_id)
        if not subject:
            await callback.answer("Дисциплина не найдена.", show_alert=True)
            return

    await state.update_data(subject_id=subject_id, old_name=subject.name)
    await callback.message.edit_text(
        f"Текущее название: <b>{subject.name}</b>\n\nВведи новое название дисциплины:"
    )
    await state.set_state(EditsubjectStates.waiting_for_name)
    await callback.answer()


@router.message(EditsubjectStates.waiting_for_name)
async def edit_subject_process(message: Message, state: FSMContext) -> None:
    """Обработка ввода нового названия дисциплины"""
    async with async_session_maker() as session:
        user = await get_user_by_tg_id(session, message.from_user.id)
        if not user or user.role != "admin":
            await message.answer("Эта функция доступна только старостам.")
            await state.clear()
            return

        data = await state.get_data()
        subject_id = data.get("subject_id")
        old_name = data.get("old_name")

        if not subject_id:
            await message.answer("Ошибка: не найден ID дисциплины. Попробуй снова.")
            await state.clear()
            return

        subject_name = message.text.strip()
        if not subject_name or len(subject_name) > 100:
            await message.answer("Название дисциплины должно быть от 1 до 100 символов. Попробуй ещё раз:")
            return

        # Проверяем, нет ли уже такой дисциплины (кроме текущей)
        existing = await list_subjects(session)
        if any(
            d.name.lower() == subject_name.lower() and d.id != subject_id
            for d in existing
        ):
            await message.answer(
                f"Дисциплина '{subject_name}' уже существует. Введи другое название:"
            )
            return

        subject = await update_subject(session, subject_id, subject_name)
        if not subject:
            await message.answer("Ошибка: дисциплина не найдена.")
            await state.clear()
            return

        await session.commit()
        subjects = await list_subjects(session)

    text = (
        f"✅ Дисциплина '<b>{old_name}</b>' переименована в '<b>{subject_name}</b>'!\n\n"
        f"📚 <b>Управление дисциплинами</b>"
    )
    await message.answer(
        text,
        reply_markup=admin_subjects_keyboard(subjects),
    )
    await state.clear()

