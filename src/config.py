from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),  # Явный путь
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=()  # Это уберет то предупреждение UserWarning из твоего лога
    )

    bot_token: str = Field(alias="BOT_TOKEN")

    db_path: str = Field(default="data/Queue_bot.db", alias="DB_PATH")

    superadmins: List[int] = Field(default_factory=list, alias="SUPERADMINS")

    @property
    def db_url(self) -> str:
        # Мы берем BASE_DIR и приклеиваем к нему db_path
        # Это гарантирует, что путь всегда будет от корня проекта
        db_full_path = BASE_DIR / self.db_path

        # Создаем директорию (например, /Queue_bot/data/), если её нет
        db_full_path.parent.mkdir(parents=True, exist_ok=True)

        # Возвращаем абсолютный путь для SQLAlchemy
        return f"sqlite+aiosqlite:///{db_full_path.absolute()}"


settings = Settings()

