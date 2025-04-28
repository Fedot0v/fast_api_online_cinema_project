# src/database/session_sqlite.py
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.config.settings import get_settings
from src.database.models.base import Base


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
DATABASE_URL = f"sqlite+aiosqlite:///{settings.PATH_TO_DB}"

logger.info(f"Connecting to database: {settings.PATH_TO_DB}")


db_dir = os.path.dirname(settings.PATH_TO_DB)
if db_dir:
    os.makedirs(db_dir, exist_ok=True)

engine = create_async_engine(DATABASE_URL, echo=False)  # Включено echo для отладки
AsyncSQLiteSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False) #type: ignore

async def init_db() -> None:
    """
    Initialize the database.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully")

async def close_db() -> None:
    """
    Close the database connection.
    """
    await engine.dispose()
    logger.info("Database connection closed")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an asynchronous database session.
    """
    async with AsyncSQLiteSessionLocal() as session:
        yield session

@asynccontextmanager
async def get_db_contextmanager() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an asynchronous database session using a context manager.
    """
    async with AsyncSQLiteSessionLocal() as session:
        yield session

async def reset_sqlite_database() -> None:
    """
    Reset the SQLite database.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database reset successfully")