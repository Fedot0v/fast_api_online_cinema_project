from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import UserModel
from src.repositories.accounts import UserRepository
from src.services.auth.activation_token_service import ActivationTokenService
from src.services.validation.user_validation_service import UserValidationService
from src.services.base import BaseService
from src.services.emails import EmailSenderService


class RegistrationService(BaseService):
    def __init__(
            self,
            user_repository: UserRepository,
            email_sender_service: EmailSenderService,
            db: AsyncSession,
            user_validation_service: UserValidationService,
            activation_token_service: ActivationTokenService
    ):
        super().__init__(db)
        self.user_repository = user_repository
        self.email_sender_service = email_sender_service
        self.user_validation_service = user_validation_service
        self.activation_token_service = activation_token_service

    async def register_user(self, email: str, password: str, group_id: int = 1) -> UserModel:
        await self.user_validation_service.validate_email_uniqueness(email)

        new_user = await self.user_repository.create_user(email, password, group_id)
        try:
            await self.user_repository.db.flush()
            await self.user_repository.db.refresh(new_user)

            activation_token = await (
                self.activation_token_service.create_activation_token(new_user)
            )
            activation_link = f"http://localhost:8000/activate/{activation_token}"  # TODO change to real url in future

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
