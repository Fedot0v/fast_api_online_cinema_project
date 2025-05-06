import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.config.settings import get_settings
from src.database import UserGroupModel, UserGroupEnum
from src.database.models.base import Base
from sqlalchemy import select


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@postgres:5432/cinema_db")

logger.info(f"Connecting to database: {DATABASE_URL}")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncPostgresSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """
    Initialize the database and populate user_groups with default groups.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")

    async with AsyncPostgresSessionLocal() as session:
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
    async with AsyncPostgresSessionLocal() as session:
        yield session


@asynccontextmanager
async def get_db_contextmanager() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an asynchronous database session using a context manager.
    """
    async with AsyncPostgresSessionLocal() as session:
        yield session 