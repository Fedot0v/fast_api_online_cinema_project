from typing import cast

from fastapi import APIRouter, Depends, status
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.accounts import get_user_service, get_activation_token_service
from src.schemas.accounts import (
    UserRegistrationSchema,
    UserRegistrationResponseSchema,
    TokenRequestSchema,
    MessageSchema
)
from src.services.accounts import UserAccountService, ActivationTokenService

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post(
    "/register/",
    response_model=UserRegistrationResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="User registration",
    description="Register a new user with an email and password.",
    responses={
        409: {
            "description": "User with this email already exists.",
            "content": {"application/json": {
                "example": {
                    "detail": "A user with this email test@example.com already exists."
                }
            }
            }
        },
        500: {
            "description": "An error occurred during registration.",
            "content": {"application/json": {
                "example": {
                    "detail": "An error occurred during registration."
                }
            }}
        },
    }
)
async def register(
        response_data: UserRegistrationSchema,
        user_service: UserAccountService = Depends(get_user_service)
) -> UserRegistrationResponseSchema:
    user = await user_service.register_user(
        email=cast(str, response_data.email),
        password=response_data.password,
        group_id=response_data.group_id
    )
    return UserRegistrationResponseSchema(
        id=user.id,
        email=cast(EmailStr, user.email),
    )


@router.post(
    "/activate/",
    response_model=dict,
    summary="User activation",
    description="Activate a user account by sending "
                "an activation link to their email address.",
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "description": "Bad Request - The activation token "
                           "is invalid or expired, "
                           "or the user account is already active.",
            "content": {"application/json": {
                "example": {
                    "invalid_token": {
                        "summary": "Invalid activation token",
                        "value": {
                            "detail": "Invalid or expired activation token."
                        }
                    },
                    "already_active": {
                        "summary": "User account already active",
                        "value": {
                            "detail": "User account is already active."
                        }
                    }
                }
            }
            }
        }
    },
    
)
async def activate_account(
        activation_data: TokenRequestSchema,
        token_service: ActivationTokenService = Depends(
            get_activation_token_service
        )
) -> MessageSchema:
    await token_service.validate_and_activate_user(activation_data.token)
    return {"message": "User account activated successfully."}


