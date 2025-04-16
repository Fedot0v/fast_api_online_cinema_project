from typing import cast

from fastapi import APIRouter, Depends, status
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.accounts import get_user_service, get_activation_token_service, get_password_reset_token_service
from src.schemas.accounts import (
    UserRegistrationSchema,
    UserRegistrationResponseSchema,
    MessageSchema,
    BaseTokenSchema, BaseEmailSchema, PasswordResetCompleteRequestSchema
)
from src.services.accounts import RegistrationService, ActivationTokenService, PasswordResetTokenService

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
        user_service: RegistrationService = Depends(get_user_service)
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
        activation_data: BaseTokenSchema,
        token_service: ActivationTokenService = Depends(
            get_activation_token_service
        )
) -> dict:
    await token_service.validate_and_activate_user(activation_data.token)
    return {"message": "User account activated successfully."}


@router.post(
    "/reset-password/request/",
    response_model=dict,
    summary="Password reset request",
    description="Request a password reset link by sending an email "
                "with a password reset link to the user's email address.",
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "description": "Bad Request - The email is invalid.",
            "content": {"application/json": {
                "example": {
                    "invalid_email": {
                        "detail": "Invalid email or token."
                    },
                    "invalid_token": {
                        "detail": "Invalid email or token."
                    }
                }
            }}
        }
    }
)
async def password_reset(
        request_data: BaseEmailSchema,
        token_service: PasswordResetTokenService = Depends(
            get_password_reset_token_service
        )
) -> dict:
    return await token_service.request_password_reset(
        cast(str, request_data.email)
    )


@router.post(
    "/reset-password/complete/",
    response_model=dict,
    summary="Password reset completion",
    description="Complete the password reset process by "
                "validating the password reset token and updating the user's password.",
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "description": (
                "Bad Request - The provided email or token is invalid, "
                "the token has expired, or the user account is not active."
            ),
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_email_or_token": {
                            "summary": "Invalid Email or Token",
                            "value": {
                                "detail": "Invalid email or token."
                            }
                        },
                        "expired_token": {
                            "summary": "Expired Token",
                            "value": {
                                "detail": "Invalid email or token."
                            }
                        }
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error - An error occurred while resetting the password.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An error occurred while resetting the password."
                    }
                }
            },
        }
    }
)
async def password_reset_complete(
        reset_data: PasswordResetCompleteRequestSchema,
        token_service: PasswordResetTokenService = Depends(
            get_password_reset_token_service
        )
) -> dict:
    return await token_service.complete_password_reset(
        cast(str, reset_data.email),
        reset_data.token,
        reset_data.password
    )
