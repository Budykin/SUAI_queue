from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings


engine = create_async_engine(
    settings.db_url,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False},  # Для SQLite
)

async_session_maker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

