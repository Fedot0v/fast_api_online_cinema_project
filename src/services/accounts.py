from datetime import timezone, datetime
from typing import cast

from fastapi import HTTPException, status
from pydantic import EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import UserModel, ActivationTokenModel
from src.repositories.accounts import UserRepository, ActivationTokenRepository, \
    PasswordResetTokenRepository
from src.security.interfaces import JWTAuthManagerInterface
from src.services.emails import EmailSenderService


class BaseAccountService:
    def __init__(
            self,
            db: AsyncSession
    ):
        self.db = db


class RegistrationService(BaseAccountService):
    def __init__(
            self,
            db: AsyncSession,
            jwt_manager: JWTAuthManagerInterface,
            email_sender_service: EmailSenderService
    ):
        super().__init__(db)
        self.jwt_manager = jwt_manager
        self.user_rep = UserRepository(db)
        self.email_sender_service = email_sender_service

    async def register_user(self, email: str, password: str, group_id: int = 1) -> UserModel:
        existing_user = await self.user_rep.get_user_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A user with this email {email} already exists."
            )

        new_user = await self.user_rep.create_user(email, password, group_id)

        try:
            await self.db.flush()
            await self.db.refresh(new_user)

            activation_token = self.jwt_manager.create_access_token(
                data={"sub": new_user.email, "type": "activation"}
            )

            token_model = ActivationTokenModel(
                user_id=new_user.id,
                token=activation_token
            )
            self.db.add(token_model)
            await self.db.commit()

            activation_link = f"http://localhost:8000/activate/{activation_token}" #TODO change to real url in future

            await self.email_sender_service.send_activation_email(
                email=new_user.email,
                activation_link=activation_link
            )

            return new_user
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A user with this email {new_user.email} already exists."
            )
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred during registration."
            )


class ActivationTokenService(BaseAccountService):
    def __init__(
            self,
            db: AsyncSession,
            email_sender_service: EmailSenderService
    ):
        super().__init__(db)
        self.token_rep = ActivationTokenRepository(db)
        self.email_sender_service = email_sender_service

    async def validate_and_activate_user(self, token: str) -> UserModel:
        activation_token = await self.token_rep.get_activation_token(token)

        if not activation_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired activation token."
            )

        expires_at_with_tz = activation_token.expires_at.replace(tzinfo=timezone.utc)
        if expires_at_with_tz < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired activation token."
            )

        user = activation_token.user

        if user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already active."
            )

        user.is_active = True
        await self.db.commit()
        await self.token_rep.delete_token(token, ActivationTokenModel)

        login_link = "http://localhost:8000/login/"
        await self.email_sender_service.send_activation_complete_email(
            email=user.email,
            login_link=login_link
        )

        return user


class PasswordResetTokenService(BaseAccountService):
    def __init__(
            self,
            db: AsyncSession,
            email_sender_service: EmailSenderService
    ):
        super().__init__(db)
        self.token_rep = PasswordResetTokenRepository(db)
        self.user_rep = UserRepository(db)
        self.email_sender_service = email_sender_service

    async def request_password_reset(self, email: str) -> dict:
        try:
            user = await self.user_rep.get_user_by_email(email)

            if user and user.is_active:
                token_list = await self.token_rep.get_token(cast(int, user.id))
                await self.token_rep.delete_tokens(token_list)
                new_token = self.token_rep.create_reset_token_instance(
                    cast(int, user.id)
                )
                self.db.add(new_token)
                await self.db.commit()

                reset_complete_link = "http://localhost:8000/reset-password-complete/"
                await self.email_sender_service.send_password_reset_email(
                    email=email,
                    reset_link=reset_complete_link
                )

            return {
                "message": "If you are registered,"
                           " you  wil receive an email with instructions."
            }
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process password reset request: {str(e)}"
            )

    async def validate_reset_token(self, email: str, token: str) -> UserModel:
        user = await self.user_rep.get_user_by_email(email)
        if not user or not user.is_active:
            token_list = await (
                self.token_rep.get_token(user.id)
            ) if user else []
            if token_list:
                await (self.token_rep.
                       delete_tokens(token_list)
                       )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email or token."
            )

        reset_token = await self.token_rep.get_by_token(token)
        if not reset_token or reset_token.user_id != user.id:
            token_list = await self.token_rep.get_token(cast(int, user.id))
            if token_list:
                await self.token_rep.delete_tokens(token_list)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email or token."
            )

        expires_at_with_tz = cast(
            datetime,
            reset_token.expires_at
        ).replace(tzinfo=timezone.utc)
        if expires_at_with_tz < datetime.now(timezone.utc):
            await self.token_rep.delete_tokens([reset_token])
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email or token."
            )
        return user

    async def complete_password_reset(
            self,
            email: str,
            token: str,
            password: str
    ) -> dict:
        try:
            user = await self.validate_reset_token(email, token)

            await self.user_rep.update_password(user, password)

            reset_token = await self.token_rep.get_by_token(token)
            if reset_token:
                await self.token_rep.delete_tokens([reset_token])

            await self.db.commit()

            login_link = "http://localhost:8000/login/"
            await self.email_sender_service.send_password_reset_complete_email(
                email=email,
                login_link=login_link
            )

            return {"message": "Password reset successful."}
        except HTTPException as e:
            await self.db.rollback()
            raise e
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred during password reset: {str(e)}."
            )
