import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from src.config import settings
from src.database.models import Base, Subject
from src.database import async_session_maker, engine
from src.handlers import start, queue, admin


async def init_db() -> bool:
    """
    Инициализирует базу данных.
    Возвращает True, если дисциплины есть, False - если нет.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Проверяем наличие дисциплин
    async with async_session_maker() as session:
        from sqlalchemy import select

        result = await session.execute(select(Subject))
        disciplines = result.scalars().all()
        if not disciplines:
            return False
        return True


async def main() -> None:
    has_disciplines = await init_db()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация роутеров
    dp.include_routers(
        start.router,
        queue.router,
        admin.router,
    )

    # Отправляем уведомление админам, если дисциплин нет
    if not has_disciplines and settings.superadmins:
        from src.database.requests import get_user_by_tg_id

        async with async_session_maker() as session:
            for admin_tg_id in settings.superadmins:
                try:
                    user = await get_user_by_tg_id(session, admin_tg_id)
                    if user and user.role == "admin":
                        await bot.send_message(
                            admin_tg_id,
                            "⚠️ <b>ВНИМАНИЕ</b>\n\n"
                            "Дисциплины не указаны в базе данных.\n"
                            "Используй кнопку '⚙️ Управление дисциплинами' в главном меню, "
                            "чтобы добавить дисциплины.",
                        )
                except Exception as e:
                    print(f"Не удалось отправить уведомление админу {admin_tg_id}: {e}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

