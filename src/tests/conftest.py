import os
# Устанавливаем тестовое окружение до импорта модулей
os.environ["ENVIRONMENT"] = "testing"

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import Settings
from src.config import get_settings
from src.database import (
    reset_sqlite_database,
    get_db_contextmanager, UserGroupEnum, UserGroupModel, ActivationTokenModel, UserModel,
)
from src.main import app
from src.providers.payment_provider import PaymentProviderInterface
from src.repositories.payments.payments_repo import PaymentsRepository
from src.services.payments.payments_service import PaymentService
from src.database.models.payments import PaymentStatusEnum


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


@pytest.fixture
def payment_provider():
    class MockPaymentProvider(PaymentProviderInterface):
        def __init__(self):
            self.payments = {}
            self.last_payment_id = None

        async def initiate_payment(self, order_id: int, amount: Decimal, currency: str) -> str:
            payment_id = f"pi_{order_id}"
            self.payments[payment_id] = {
                "id": payment_id,
                "amount": amount,
                "status": "requires_payment_method"
            }
            self.last_payment_id = payment_id
            return f"https://payment.test/{payment_id}"

        async def get_payment_intent(self, payment_id: str) -> dict:
            if payment_id not in self.payments:
                if payment_id.startswith("pi_"):
                    self.payments[payment_id] = {
                        "id": payment_id,
                        "amount": Decimal("100.00"),
                        "status": "succeeded"
                    }
            return self.payments.get(payment_id, {"id": payment_id, "status": "succeeded"})

        async def complete_payment(self, payment_id: str) -> bool:
            if payment_id not in self.payments:
                if payment_id.startswith("pi_"):
                    self.payments[payment_id] = {
                        "id": payment_id,
                        "amount": Decimal("100.00"),
                        "status": "succeeded"
                    }
            if payment_id in self.payments:
                self.payments[payment_id]["status"] = "succeeded"
            return True

        async def refund_payment(self, payment_id: str, amount: Optional[Decimal] = None) -> bool:
            if payment_id not in self.payments:
                if payment_id.startswith("pi_"):
                    self.payments[payment_id] = {
                        "id": payment_id,
                        "amount": Decimal("100.00"),
                        "status": "succeeded"
                    }
            if payment_id in self.payments and self.payments[payment_id]["status"] == "succeeded":
                self.payments[payment_id]["status"] = "refunded"
                return True
            return True

        def get_last_payment_intent_id(self) -> Optional[str]:
            return self.last_payment_id

    return MockPaymentProvider()


@pytest_asyncio.fixture
async def payment_repository(db_session):
    from src.repositories.payments.payments_repo import PaymentsRepository
    return PaymentsRepository(db_session)


@pytest_asyncio.fixture
async def cart_repository(db_session):
    from src.repositories.cart.cart_rep import CartRepository
    return CartRepository(db_session)


@pytest_asyncio.fixture
async def order_repository(db_session):
    from src.repositories.orders.order_repo import OrderRepository
    return OrderRepository(db_session)


@pytest_asyncio.fixture
async def payment_service(
    payment_repository,
    cart_repository,
    order_repository,
    payment_provider
):
    return PaymentService(
        payment_repository=payment_repository,
        cart_repository=cart_repository,
        order_repository=order_repository,
        payment_provider=payment_provider
    )


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a test user for payment tests."""
    user = UserModel.create(
        email="test_payment@example.com",
        raw_password="TestPassword123!",
        group_id=1,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def movie_repository(db_session):
    from src.repositories.movies.movies import MovieRepository
    return MovieRepository(db_session)


@pytest_asyncio.fixture
async def admin_token(client, db_session):
    """Create an admin user and return their access token."""
    admin_group = UserGroupModel(name=UserGroupEnum.ADMIN.value)
    db_session.add(admin_group)
    await db_session.commit()

    admin = UserModel.create(
        email="admin@example.com",
        raw_password="AdminPassword123!",
        group_id=admin_group.id,
    )
    db_session.add(admin)
    await db_session.commit()

    admin.is_active = True
    await db_session.commit()

    response = await client.post(
        "/api/v1/accounts/login/",
        data={
            "username": "admin@example.com",
            "password": "AdminPassword123!"
        }
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def regular_user_token(client, db_session):
    """Create a regular user and return their access token."""
    user_group = UserGroupModel(name=UserGroupEnum.USER.value)
    db_session.add(user_group)
    await db_session.commit()

    user = UserModel.create(
        email="user@example.com",
        raw_password="UserPassword123!",
        group_id=user_group.id,
    )
    db_session.add(user)
    await db_session.commit()

    user.is_active = True
    await db_session.commit()

    response = await client.post(
        "/api/v1/accounts/login/",
        data={
            "username": "user@example.com",
            "password": "UserPassword123!"
        }
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def test_movie(db_session):
    """
    Create a test movie in the database.
    """
    from src.database.models.movies import MovieModel
    movie = MovieModel(
        title="Test Movie",
        year=2024,
        time=120,
        imdb=8.0,
        meta_score=75.0,
        description="Test description",
        price=Decimal("9.99"),
        certification_id=1
    )
    db_session.add(movie)
    await db_session.commit()
    await db_session.refresh(movie)
    return movie


@pytest_asyncio.fixture
async def test_certification(db_session):
    """
    Create a test certification in the database.
    """
    from src.database.models.movies import CertificationModel
    certification = CertificationModel(name="PG-13")
    db_session.add(certification)
    await db_session.commit()
    await db_session.refresh(certification)
    return certification


@pytest_asyncio.fixture
async def test_cart(db_session, regular_user_token, admin_token):
    """
    Create test carts for both regular user and admin.
    """
    from src.database.models.cart import CartModel
    from src.database.models.accounts import UserModel
    from sqlalchemy import select
    
    users = await db_session.execute(
        select(UserModel).where(
            UserModel.email.in_(["user@example.com", "admin@example.com"])
        )
    )
    users = users.scalars().all()
    
    carts = []
    for user in users:
        cart = CartModel(user_id=user.id)
        db_session.add(cart)
        carts.append(cart)
    
    await db_session.commit()
    for cart in carts:
        await db_session.refresh(cart)
    
    return next(cart for cart in carts if cart.user_id == users[0].id)
