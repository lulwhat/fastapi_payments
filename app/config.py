import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SQL_USER: str
    SQL_PASSWORD: str
    SQL_DATABASE: str
    SECRET_KEY: str
    WEBHOOK_SECRET_KEY: str

    @property
    def URL_DATABASE(self) -> str:
        db_host = os.getenv("DB_HOST", "localhost")
        return (f'postgresql+asyncpg://{self.SQL_USER}:{self.SQL_PASSWORD}'
                f'@{db_host}:5432/{self.SQL_DATABASE}')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
