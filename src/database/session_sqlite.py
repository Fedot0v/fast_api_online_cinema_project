from contextlib import asynccontextmanager
from typing import AsyncGenerator
import os
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.config.settings import get_settings
from src.database import UserGroupModel, UserGroupEnum
from src.database.models.base import Base


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
DATABASE_URL = f"sqlite+aiosqlite:///{settings.PATH_TO_DB}"

logger.info(f"Connecting to database: {settings.PATH_TO_DB}")


db_dir = os.path.dirname(settings.PATH_TO_DB)
if db_dir:
    os.makedirs(db_dir, exist_ok=True)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSQLiteSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False) #type: ignore


async def init_db() -> None:
    """
    Initialize the database and populate user_groups with default groups.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")

    async with AsyncSQLiteSessionLocal() as session:
        stmt = select(UserGroupModel)
        result = await session.execute(stmt)
        groups = result.scalars().all()

        if not groups:
            logger.info("Populating user_groups with default groups: user, admin, moderator")
            default_groups = [
                UserGroupModel(name=UserGroupEnum.USER),
                UserGroupModel(name=UserGroupEnum.ADMIN),
                UserGroupModel(name=UserGroupEnum.MODERATOR)
            ]
            session.add_all(default_groups)
            await session.commit()
            logger.info("Default groups created successfully")
        else:
            logger.info(f"user_groups already contains groups: {[g.name for g in groups]}")


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