from datetime import date
from typing import Type, List

from fastapi import HTTPException, status
from sqlalchemy import select, delete, update
from sqlalchemy.orm import joinedload

from src.database.models.accounts import UserModel, GenderEnum, UserProfileModel, RefreshTokenModel, ActivationTokenModel, \
    PasswordResetTokenModel, TokenBaseModel
from src.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    async def create_user(
            self,
            email: str,
            raw_password: str,
            group_id: int
    ) -> UserModel:
        user = UserModel.create(email, raw_password, group_id)
        self.db.add(user)
        return user

    async def get_user_by_email(self, email: str) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_user_by_id(self, user_id: int) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def update_password(
            self,
            user: UserModel,
            new_password: str
    ) -> UserModel:
        try:
            user.password = new_password
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except ValueError as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid password: {str(e)}"
            )
        except Exception:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred during password update."
            )


class BaseTokenRepository(BaseRepository):

    async def delete_token(
            self,
            token_value: str,
            token_model: Type[TokenBaseModel]
    ) -> None:
        stmt = delete(token_model).where(token_model.token == token_value)
        await self.db.execute(stmt)


class ActivationTokenRepository(BaseTokenRepository):

    async def get_activation_token(
            self,
            token_value: str
    ) -> ActivationTokenModel | None:
        stmt = select(ActivationTokenModel).where(
            ActivationTokenModel.token == token_value
        ).options(joinedload(ActivationTokenModel.user))

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


class PasswordResetTokenRepository(BaseTokenRepository):

    async def get_token(
            self,
            user_id: int
    ) -> List[PasswordResetTokenModel]:
        stmt = select(PasswordResetTokenModel).where(
            PasswordResetTokenModel.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete_tokens(
            self,
            tokens: List[PasswordResetTokenModel]
    ) -> None:
        for token in tokens:
            await self.db.delete(token)
        await self.db.commit()

    @staticmethod
    def create_reset_token_instance(
            user_id: int
    ) -> PasswordResetTokenModel:
        return PasswordResetTokenModel(user_id=user_id)

    async def get_by_token(
            self,
            token: str
    ) -> PasswordResetTokenModel | None:
        stmt = select(PasswordResetTokenModel).where(
            PasswordResetTokenModel.token == token
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


class RefreshTokenRepository(BaseTokenRepository):
    async def get_refresh_token(self, token: str) -> RefreshTokenModel | None:
        stmt = select(RefreshTokenModel).where(
            RefreshTokenModel.token == token
        ).options(joinedload(RefreshTokenModel.user))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()