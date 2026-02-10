"""Подключение к базе данных."""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import Config
from database.models import Base

# Глобальные переменные для подключения
engine = None
async_session_maker = None


async def init_db(config: Config) -> None:
    """Инициализирует подключение к базе данных."""
    global engine, async_session_maker
    
    # Создаем async engine
    database_url = config.get_async_db_url()
    engine = create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
    )
    
    # Создаем session maker
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Получает сессию базы данных."""
    if async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_db() -> None:
    """Закрывает подключение к базе данных."""
    global engine
    if engine:
        await engine.dispose()
