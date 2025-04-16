from datetime import timezone, datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import UserModel, ActivationTokenModel
from src.repositories.accounts import UserRepository, TokenRepository
from src.security.interfaces import JWTAuthManagerInterface


class BaseAccountService:
    def __init__(
            self,
            db: AsyncSession
    ):
        self.db = db


class UserAccountService(BaseAccountService):
    def __init__(
            self,
            db: AsyncSession,
            jwt_manager: JWTAuthManagerInterface
    ):
        super().__init__(db)
        self.jwt_manager = jwt_manager
        self.user_rep = UserRepository(db)

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
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.token_rep = TokenRepository(db)

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

        return user
