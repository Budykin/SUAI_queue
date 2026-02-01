from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from src.config import settings
from src.database import async_session_maker
from src.database.requests import (
    ensure_admin_roles,
    create_user,
    get_user_by_tg_id,
)
from src.keyboards.reply import main_menu_keyboard

router = Router()

class Register(StatesGroup):
    waiting_for_name = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    async with async_session_maker() as session:
        user = await get_user_by_tg_id(
            session=session,
            tg_id=message.from_user.id
        )
        if user:
            await ensure_admin_roles(session, settings.superadmins)
            await session.commit()
            is_admin = user.role == "admin"
            text = (
                "Привет! Я бот для управления очередью студентов.\n\n"
                "Используй меню ниже, чтобы выбрать дисциплину и посмотреть свои очереди."
            )
            await message.answer(text, reply_markup=main_menu_keyboard(is_admin=is_admin))
        else:
            # Если юзера нет, просим имя и переходим в состояние ожидания
            await message.answer("Привет! Давай знакомиться. Введи свои Фамилию и Имя:")
            await state.set_state(Register.waiting_for_name)


@router.message(Register.waiting_for_name)
async def process_name(message: Message, state: FSMContext) -> None:
    full_name = message.text.strip()

    if len(full_name) < 2:
        await message.answer("Имя слишком короткое. Введи имя полностью:")
        return

    async with async_session_maker() as session:
        # Создаем пользователя с введенным именем
        user = await create_user(
            session=session,
            tg_id=message.from_user.id,
            full_name=full_name
        )
        await ensure_admin_roles(session, settings.superadmins)
        await session.commit()
        # Обновляем объект пользователя, чтобы узнать его новую роль
        await session.refresh(user)
        is_admin = user.role == "admin"

    await state.clear()  # Выключаем состояние ожидания

    text = (
        f"Приятно познакомиться, {full_name}!\n\n"
        "Я бот для управления очередью. Используй меню ниже, чтобы выбрать дисциплину и посмотреть свои очереди."
    )
    await message.answer(text, reply_markup=main_menu_keyboard(is_admin=is_admin))