from typing import cast

from fastapi import APIRouter, Depends, status
from pydantic import EmailStr

from src.dependencies.accounts import get_user_service, get_activation_token_service, get_password_reset_token_service, \
    get_register_service, get_user_auth_service, get_admin_service
from src.dependencies.auth import require_permissions, get_current_user
from src.schemas.accounts import (
    UserRegistrationSchema,
    UserRegistrationResponseSchema,
    MessageSchema,
    BaseTokenSchema, BaseEmailSchema, PasswordResetCompleteRequestSchema, LoginResponseSchema, LoginRequestSchema,
    RefreshTokenSchema, AccessTokenSchema
)
from src.services.auth.activation_token_service import ActivationTokenService
from src.services.auth.admin_service import AdminService
from src.services.auth.password_reset_token_service import PasswordResetTokenService
from src.services.auth.registration_service import RegistrationService
from src.services.auth.user_auth_service import UserAuthService
from src.services.auth.user_service import UserService

router = APIRouter()


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
        register_service: RegistrationService = Depends(get_register_service)
) -> UserRegistrationResponseSchema:
    user = await register_service.register_user(
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
        ),
        user_service: UserService = Depends(get_user_service)
) -> dict:
    await token_service.process_activation(activation_data.token, user_service)
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


@router.post(
    "/login/",
    response_model=LoginResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Log in a user account by providing their email and password.",
    responses={
        401: {
            "description": "Unauthorized - Invalid email or password.",
            "content": {"application/json": {
                "example": {
                    "detail": "Invalid email or password."
                }
            }}
        },
        403: {
            "description": "Forbidden - User account is not active.",
            "content": {"application/json": {
                "example": {
                    "detail": "User is not active."
                }
            }}
        }

    }
)
async def login(
        login_data: LoginRequestSchema,
        user_service: UserAuthService = Depends(get_user_auth_service)
) -> LoginResponseSchema:
    response = await user_service.login_user(
        cast(str, login_data.email),
        cast(str, login_data.password)
    )
    return LoginResponseSchema(**response)


@router.post(
    "/refresh/",
    response_model=RefreshTokenSchema,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Refresh the access token by providing a valid refresh token.",
    responses={
        400: {
            "description": "Bad Request - The refresh token is invalid or expired.",
            "content": {"application/json": {
                "example": {
                    "expired_token": {
                        "summary": "Expired Token",
                        "detail": "Token has expired."
                    },
                    "invalid_token": {
                        "summary": "Invalid Token",
                        "detail": "Invalid refresh token."
                    }
                }
            }}
        },
        401: {
            "description": "Unauthorized - Invalid refresh token.",
            "content": {"application/json": {
                "example": {
                    "detail": "Refresh token not found."
                }
            }}
        },
        404: {
            "description": "Not Found - User not found.",
            "content": {"application/json": {
                "example": {
                    "detail": "User not found."
                }
            }}
        },
        500: {
            "description": "Internal Server Error - An error occurred during refresh.",
            "content": {"application/json": {
                "example": {
                    "detail": "An error occurred during refresh."
                }
            }}
        }
    }
)
async def refresh_access_token(
        refresh_data: RefreshTokenSchema,
        user_service: UserAuthService = Depends(get_user_service)
) -> AccessTokenSchema:
    response = await user_service.refresh_access_token(
        cast(str, refresh_data.refresh_token)
    )
    return AccessTokenSchema(**response)


@router.post(
    "/logout/",
    response_model=MessageSchema,
    status_code=status.HTTP_200_OK,
    summary="User logout",
    description="Log out a user by invalidating their refresh token.",
    responses={
        401: {
            "description": "Unauthorized - Invalid or missing refresh token.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid refresh token."}
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred during logout.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred during logout."}
                }
            }
        }
    }
)
async def logout(
    token_data: RefreshTokenSchema,
    user_service: UserAuthService = Depends(get_user_service)
) -> MessageSchema:
    return await user_service.logout_user(token_data.refresh_token)


@router.post(
    "/change-group/",
    response_model=MessageSchema,
    status_code=status.HTTP_200_OK,
    summary="Change user group",
    description="Manually change the group of a user by admin.",
    responses={
        404: {
            "description": "Not Found - User not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "User not found."}
                }
            }
        },
        400: {
            "description": "Bad Request - The provided group ID is invalid.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid group ID."}
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred during group change.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred during group change."}
                }
            }
        }
    },
    dependencies=[Depends(require_permissions(["manage_users"]))]
)
async def change_group(
        user_id: int,
        new_group_id: int,
        current_user: dict = Depends(get_current_user),
        admin_service: AdminService = Depends(get_admin_service)
) -> MessageSchema:
    await admin_service.change_user_group(user_id, new_group_id, current_user["user_id"])
    return MessageSchema(message="User group changed successfully.")


@router.post(
    "/manual-activate/",
    response_model=MessageSchema,
    responses={
        404: {
            "description": "Not Found - User not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "User not found."}
                }
            }
        },
        400: {
            "description": "Bad Request - User is already active.",
            "content": {
                "application/json": {
                    "example": {"detail": "User is already active."}
                }
            }
        },
        500: {
            "description": "Internal Server Error - An error occurred during activation.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred during activation."}
                }
            }
        }
    },
    dependencies=[Depends(require_permissions(["manage_users"]))]
)
async def manual_activate(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    await admin_service.manually_activate_user(user_id, current_user["user_id"])
    return MessageSchema(message="Account activated successfully")
