import logging
from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database import UserProfileModel
from src.database.models.accounts import GenderEnum
from src.exceptions.profiles import ProfileNotFoundError, ProfileCreationError, ProfileUpdateError
from src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class ProfileRepository(BaseRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def check_profile_exists(self, user_id: int) -> bool:
        logger.info(f"Checking if profile exists for user {user_id}")
        stmt = select(UserProfileModel).where(UserProfileModel.user_id == user_id)
        result = await self.db.execute(stmt)
        profile = result.scalars().first()
        exists = profile is not None
        logger.info(f"Profile exists for user {user_id}: {exists}")
        return exists

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
        logger.info(f"Creating profile for user {user_id}")
        try:
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
            await self.db.flush()
            logger.info(f"Profile for user {user_id} created")
            return profile
        except Exception as e:
            logger.error(f"Error creating profile for user {user_id}: {str(e)}")
            raise ProfileCreationError(user_id, str(e))

    async def get_profile_by_user_id(self, user_id: int) -> UserProfileModel:
        logger.info(f"Getting profile for user {user_id}")
        profile = await self.db.get(UserProfileModel, user_id)
        if not profile:
            logger.error(f"Profile for user {user_id} not found")
            raise ProfileNotFoundError(user_id)
        logger.info(f"Profile for user {user_id} retrieved")
        return profile

    async def update_profile(self, profile: UserProfileModel, updates: dict[str, Any]) -> UserProfileModel:
        logger.info(f"Updating profile for user {profile.user_id}")
        try:
            for field, value in updates.items():
                if hasattr(profile, field):
                    setattr(profile, field, value)
                else:
                    logger.warning(f"Attempted to update non-existent field {field} for user {profile.user_id}")
            await self.db.flush()
            logger.info(f"Profile for user {profile.user_id} updated successfully")
            return profile
        except Exception as e:
            logger.error(f"Error updating profile for user {profile.user_id}: {str(e)}")
            raise ProfileUpdateError(profile.user_id, str(e))
