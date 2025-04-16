from datetime import date, datetime, timezone
from typing import Type, Sequence

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database.models.accounts import UserModel, GenderEnum, UserProfileModel, RefreshTokenModel, ActivationTokenModel, \
    PasswordResetTokenModel, TokenBaseModel


class BaseAccountRepository:
    def __init__(
            self,
            db: AsyncSession,
    ):
        self.db = db


class UserRepository(BaseAccountRepository):
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


class ProfileRepository(BaseAccountRepository):
    async def create_profile(
            self,
            user_id: int,
            first_name: str,
            last_name: str,
            avatar: str,
            gender: GenderEnum,
            date_of_birth: date | None = None,
            info: str | None = None
    ) -> UserProfileModel:
        profile = UserProfileModel(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            avatar=avatar,
            gender=gender,
            date_of_birth=date_of_birth,
            info=info
        )
        self.db.add(profile)
        return profile

    async def update_profile(
            self,
            user_id: int,
            first_name: str | None = None,
            last_name: str | None = None,
            avatar: str | None = None,
            gender: GenderEnum | None = None,
            date_of_birth: date | None = None,
            info: str | None = None
    ) -> UserProfileModel:
        stmt = select(UserProfileModel).where(
            UserProfileModel.user_id == user_id
        )
        result = await self.db.execute(stmt)
        profile = result.scalars().first()

        if profile:
            updates = {}
            if first_name is not None:
                updates["first_name"] = first_name
            if last_name is not None:
                updates["last_name"] = last_name
            if avatar is not None:
                updates["avatar"] = avatar
            if gender is not None:
                updates["gender"] = gender
            if date_of_birth is not None:
                updates["date_of_birth"] = date_of_birth
            if info is not None:
                updates["info"] = info
            if updates:
                stmt = update(UserProfileModel).where(
                    UserProfileModel.user_id == user_id
                ).values(**updates)
                await self.db.execute(stmt)

            await self.db.refresh(profile)
        return profile

    async def get_profile_by_user_id(
            self,
            user_id: int
    ) -> UserProfileModel | None:
        stmt = select(UserProfileModel).where(UserProfileModel.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()


class TokenRepository(BaseAccountRepository):
    async def create_refresh_token(
            self,
            user_id: int,
            days_valid: int,
            token: str
    ) -> RefreshTokenModel:
        token_obj = RefreshTokenModel.create(
            user_id=user_id,
            days_valid=days_valid,
            token=token
        )
        self.db.add(token_obj)
        return token_obj

    async def delete_expired_tokens(self) -> None:
        now = datetime.now(timezone.utc)
        await self.db.execute(
            delete(ActivationTokenModel)
            .where(ActivationTokenModel.expires_at < now)
        )
        await self.db.execute(
            delete(PasswordResetTokenModel)
            .where(PasswordResetTokenModel.expires_at < now)
        )
        await self.db.execute(
            delete(RefreshTokenModel)
            .where(RefreshTokenModel.expires_at < now)
        )

    async def get_active_refresh_tokens(
            self,
            user_id: int
    ) -> Sequence[RefreshTokenModel]:
        stmt = select(RefreshTokenModel).where(
            RefreshTokenModel.user_id == user_id,
            RefreshTokenModel.expires_at > datetime.now(timezone.utc)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_activation_token(
            self,
            token_value: str
    ) -> ActivationTokenModel | None:
        stmt = select(ActivationTokenModel).where(
            ActivationTokenModel.token == token_value
        ).options(joinedload(ActivationTokenModel.user))

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_password_reset_token(self, token_value: str) -> PasswordResetTokenModel | None:
        stmt = select(PasswordResetTokenModel).where(PasswordResetTokenModel.token == token_value)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_refresh_token(self, token_value: str) -> RefreshTokenModel | None:
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.token == token_value)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def delete_token(
            self,
            token_value: str,
            token_model: Type[TokenBaseModel]
    ) -> None:
        stmt = delete(token_model).where(token_model.token == token_value)
        await self.db.execute(stmt)