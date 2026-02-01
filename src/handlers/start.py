from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.config import settings
from src.database import async_session_maker
from src.database.requests import ensure_admin_roles, get_or_create_user
from src.keyboards.reply import main_menu_keyboard


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    async with async_session_maker() as session:
        user = await get_or_create_user(
            session=session,
            tg_id=message.from_user.id,
            full_name=message.from_user.full_name or message.from_user.username or "Без имени",
        )

        # Обновляем роли старост из настроек
        await ensure_admin_roles(session, settings.superadmins)
        await session.commit()

    text = (
        "Привет! Я бот для управления очередью студентов.\n\n"
        "Используй меню ниже, чтобы выбрать дисциплину, посмотреть свои очереди или получить помощь."
    )
    is_admin = user.role == "admin"
    await message.answer(text, reply_markup=main_menu_keyboard(is_admin=is_admin))


@router.message(F.text == "Помощь")
async def cmd_help(message: Message) -> None:
    async with async_session_maker() as session:
        user = await get_or_create_user(
            session=session,
            tg_id=message.from_user.id,
            full_name=message.from_user.full_name or message.from_user.username or "Без имени",
        )
        is_admin = user.role == "admin"

    text = (
        "📚 <b>Помощь</b>\n\n"
        "• <b>Выбрать дисциплину</b> — выбери предмет и посмотри очередь.\n"
        "• <b>Мои очереди</b> — покажет список дисциплин, где ты уже стоишь в очереди.\n"
        "• <b>Очистить очередь</b> — доступно только старостам (админам) для конкретной дисциплины."
    )
    if is_admin:
        text += "\n• <b>Управление дисциплинами</b> — добавление и удаление дисциплин (только для админов)."
    await message.answer(text, reply_markup=main_menu_keyboard(is_admin=is_admin))

