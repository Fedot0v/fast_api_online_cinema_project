from datetime import datetime, timezone, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from src.database import UserModel, ActivationTokenModel, PasswordResetTokenModel


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, user_data: dict, db_session):
    response = await client.post(
        "/api/v1/accounts/register/",
        json=user_data
    )
    print(response)
    assert response.status_code == 201, "Expected status code 201 Created."
    response_data = response.json()
    assert response_data["email"] == user_data["email"], "Returned email does not match."
    assert "id" in response_data, "Response does not contain user ID."

    stmt_user = select(UserModel).where(UserModel.email == user_data["email"])
    result = await db_session.execute(stmt_user)
    created_user = result.scalars().first()
    assert created_user is not None, "User was not created in the database."
    assert created_user.email == user_data["email"], "Created user's email does not match."

    stmt_token = select(ActivationTokenModel).where(ActivationTokenModel.user_id == created_user.id)
    result = await db_session.execute(stmt_token)
    activation_token = result.scalars().first()
    assert activation_token is not None, "Activation token was not created in the database."
    assert activation_token.user_id == created_user.id, "Activation token's user_id does not match."
    assert activation_token.token is not None, "Activation token has no token value."

    expires_at = activation_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    assert expires_at > datetime.now(timezone.utc), "Activation token is already expired."


@pytest.mark.asyncio
async def test_register_user_conflict(client, db_session, seed_user_groups, user_data):
    """
    Test user registration conflict.

    Ensures that trying to register a user with an existing email
    returns a 409 Conflict status and the correct error message.

    Args:
        client: The asynchronous HTTP client fixture.
        db_session: The asynchronous database session fixture.
        seed_user_groups: Fixture that seeds default user groups.
    """

    response_first = await client.post("/api/v1/accounts/register/", json=user_data)
    assert response_first.status_code == 201, "Expected status code 201 for the first registration."

    stmt = select(UserModel).where(UserModel.email == user_data["email"])
    result = await db_session.execute(stmt)
    created_user = result.scalars().first()
    assert created_user is not None, "User should be created after the first registration."

    response_second = await client.post("/api/v1/accounts/register/", json=user_data)
    assert response_second.status_code == 409, "Expected status code 409 for a duplicate registration."

    response_data = response_second.json()
    expected_message = f"A user with this email {user_data['email']} already exists."
    assert response_data["detail"] == expected_message, f"Expected error message: {expected_message}"


@pytest.mark.asyncio
async def test_activate_account_expired_token(client: AsyncClient, expired_activation_token):
    """
    Test activation with an expired token.
    """
    response = await client.post(
        "/api/v1/accounts/activate/",
        json={"token": expired_activation_token.token}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired activation token."


@pytest.mark.asyncio
async def test_activate_account_already_active(client: AsyncClient, registered_user, db_session):
    """
    Test activation for an already active user.
    """
    registered_user.is_active = True
    await db_session.commit()

    token = ActivationTokenModel(
        token="valid-token-for-active-user",
        user_id=registered_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    db_session.add(token)
    await db_session.commit()

    response = await client.post(
        "/api/v1/accounts/activate/",
        json={"token": token.token}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "User is already active."


@pytest.mark.asyncio
async def test_request_password_reset_success(client: AsyncClient, registered_user, db_session):
    registered_user.is_active = True
    await db_session.commit()
    response = await client.post(
        "/api/v1/accounts/reset-password/request/",
        json={"email": registered_user.email}
    )
    assert response.status_code == 200
    assert response.json()["message"] == ("If you are registered, "
                                          "you  wil receive an email with instructions."
                                          )

    stmt = select(PasswordResetTokenModel).where(PasswordResetTokenModel.user_id == registered_user.id)
    result = await db_session.execute(stmt)
    token = result.scalar_one_or_none()
    assert token is not None
    assert token.user_id == registered_user.id
    assert token.expires_at.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc)

@pytest.mark.asyncio
async def test_request_password_reset_inactive_user(client: AsyncClient, registered_user, db_session):
    registered_user.is_active = False
    await db_session.commit()
    response = await client.post(
        "/api/v1/accounts/reset-password/request/",
        json={"email": registered_user.email}
    )
    assert response.status_code == 200
    assert response.json()["message"] == ("If you are registered, "
                                          "you  wil receive an email with instructions."
                                          )

    stmt = select(PasswordResetTokenModel).where(PasswordResetTokenModel.user_id == registered_user.id)
    result = await db_session.execute(stmt)
    token = result.scalar_one_or_none()
    assert token is None

@pytest.mark.asyncio
async def test_request_password_reset_nonexistent_email(client: AsyncClient):
    response = await client.post(
        "/api/v1/accounts/reset-password/request/",
        json={"email": "nonexistent@example.com"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == ("If you are registered, "
                                          "you  wil receive an email with instructions."
                                          )