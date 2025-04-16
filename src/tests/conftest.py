from datetime import datetime, timedelta, timezone

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.database import (
    reset_sqlite_database,
    get_db_contextmanager, UserGroupEnum, UserGroupModel, ActivationTokenModel, UserModel,
)
from src.main import app


@pytest_asyncio.fixture(scope="function", autouse=True)
async def reset_db():
    """
    Reset the SQLite database before each test.

    This fixture ensures that the database is cleared and recreated for every test function.
    It helps maintain test isolation by preventing data leakage between tests.
    """
    await reset_sqlite_database()


@pytest_asyncio.fixture(scope="function")
async def client():
    """Provide an asynchronous test client for making HTTP requests."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        yield async_client


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """
    Provide an async database session for database interactions.

    This fixture yields an async session using `get_db_contextmanager`, ensuring that the session
    is properly closed after each test.
    """
    async with get_db_contextmanager() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def user_data():
    """
    Provide default user data for tests.
    """
    return {
        "email": "testuser@example.com",
        "password": "TestPassword123!",
        "group_id": 1
    }


@pytest_asyncio.fixture(scope="function")
async def seed_user_groups(db_session: AsyncSession):
    """
    Asynchronously seed the UserGroupModel table with default user groups.

    This fixture inserts all user groups defined in UserGroupEnum into the database and commits the transaction.
    It then yields the asynchronous database session for further testing.
    """
    groups = [{"name": group.value} for group in UserGroupEnum]
    await db_session.execute(insert(UserGroupModel).values(groups))
    await db_session.commit()
    yield db_session


@pytest_asyncio.fixture(scope="function")
async def registered_user(db_session):
    """
    Create a registered user in the database.
    """
    user = UserModel.create(
        email="testuser@example.com",
        raw_password="TestPassword123!",
        group_id=1,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def activation_token(db_session, registered_user):
    """
    Create an activation token for the registered user.
    """
    token = ActivationTokenModel(
        token="valid-token",
        user_id=registered_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    db_session.add(token)
    await db_session.commit()
    await db_session.refresh(token)
    return token


@pytest_asyncio.fixture(scope="function")
async def expired_activation_token(db_session, registered_user):
    """
    Create an expired activation token for the registered user.
    """
    token = ActivationTokenModel(
        token="expired-token",
        user_id=registered_user.id,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    db_session.add(token)
    await db_session.commit()
    await db_session.refresh(token)
    return token
