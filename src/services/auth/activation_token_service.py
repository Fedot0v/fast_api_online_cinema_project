from datetime import timezone, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import ActivationTokenModel, UserModel
from src.repositories.accounts import ActivationTokenRepository
from src.security.interfaces import JWTAuthManagerInterface
from src.services.auth.user_service import UserService
from src.services.base import BaseService
from src.services.emails import EmailSenderService


class ActivationTokenService(BaseService):
    def __init__(
            self,
            db: AsyncSession,
            jwt_manager: JWTAuthManagerInterface,
            token_repository: ActivationTokenRepository,
            email_sender_service: EmailSenderService,
    ):
        super().__init__(db)
        self.jwt_manager = jwt_manager
        self.token_repository = token_repository
        self.email_sender_service = email_sender_service,

    async def create_activation_token(self, user):
        activation_token = self.jwt_manager.create_access_token(
            data={"sub": user.email, "type": "activation"}
        )

        token_model = ActivationTokenModel(
            user_id=user.id,
            token=activation_token
        )
        self.db.add(token_model)
        await self.db.commit()

        return activation_token

    async def _validate_activation_token(self, token: str) -> UserModel:
        activation_token = await self.token_repository.get_activation_token(token)
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
        return activation_token.user

    async def process_activation(self, token: str, user_service: UserService) -> None:
        user = await self._validate_activation_token(token)
        await user_service.activate_user_account(user)
        await self.token_repository.delete_token(token, ActivationTokenModel)

        login_link = "http://localhost:8000/login/"
        await self.email_sender_service.send_activation_complete_email(
            user.email,
            login_link
        )
