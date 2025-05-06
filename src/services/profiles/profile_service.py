import logging
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from src.config.settings import get_settings
from src.database import UserProfileModel
from src.exceptions.profiles import ProfileCreationError, ProfileNotFoundError, ProfileUpdateError
from src.repositories.accounts.profiles import ProfileRepository
from src.schemas.accounts import ProfileCreateSchema, UpdateProfileSchema


logger = logging.getLogger(__name__)

class ProfileService:
    def __init__(self, profile_repository: ProfileRepository):
        self.profile_repository = profile_repository
        self.upload_dir = Path("static/avatars")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.settings = get_settings()
        self.base_url = self.settings.BASE_URL
        logger.debug(f"Initialized ProfileService with BASE_URL: {self.base_url}")

    async def check_profile_exists(self, user_id: int) -> bool:
        logger.debug(f"Checking if profile exists for user_id: {user_id}")
        return await self.profile_repository.check_profile_exists(user_id)

    async def _save_uploaded_file(self, file: UploadFile) -> str:
        try:
            file_extension = file.filename.rsplit(".", 1)[1] \
                if "." in file.filename else "jpg"
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = self.upload_dir / unique_filename
            logger.debug(f"Saving uploaded file to: {file_path}")
            with file_path.open("wb") as buffer:
                content = await file.read()
                buffer.write(content)
            return file_path.as_posix()
        except Exception as e:
            logger.error(f"Error saving uploaded file: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to save avatar"
            )

    async def create_profile(
        self,
        user_id: int,
        data: ProfileCreateSchema
    ) -> UserProfileModel:
        logger.info(f"Creating profile for user_id: {user_id}")
        try:
            if await self.check_profile_exists(user_id):
                logger.warning(f"Profile already exists for user_id: {user_id}")
                raise HTTPException(status_code=400, detail="Profile already exists")

            avatar_path = None
            if data.avatar:
                avatar_path = await self._save_uploaded_file(data.avatar)
                logger.debug(f"Avatar path: {avatar_path}")

            profile = await self.profile_repository.create_profile(
                user_id=user_id,
                first_name=data.first_name,
                last_name=data.last_name,
                avatar=avatar_path,
                gender=data.gender,
                date_of_birth=data.date_of_birth,
                info=data.info
            )

            logger.debug(f"Profile created: {profile.__dict__}")
            if profile.avatar:
                try:
                    profile.avatar = f"{self.base_url}/{profile.avatar}"
                    logger.debug(f"Transformed avatar to URL: {profile.avatar}")
                except Exception as e:
                    logger.error(f"Error transforming avatar URL: {str(e)}")
                    raise

            return profile
        except ProfileCreationError as e:
            logger.error(f"Failed to create profile: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error creating profile for user_id {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create profile")

    async def update_profile(self, user_id: int, data: UpdateProfileSchema) -> UserProfileModel:
        logger.info(f"Updating profile for user_id: {user_id}")
        try:
            profile = await self.profile_repository.get_profile_by_user_id(user_id)
            updates = data.model_dump(exclude_unset=True, exclude={"avatar"})
            if data.avatar is not None:
                updates["avatar"] = await self._save_uploaded_file(data.avatar)
            profile = await self.profile_repository.update_profile(profile, updates)
            if profile.avatar:
                profile.avatar = f"{self.base_url}/{profile.avatar}"
            return profile
        except ProfileNotFoundError as e:
            logger.error(f"Profile not found: {str(e)}")
            raise HTTPException(status_code=404, detail=str(e))
        except ProfileUpdateError as e:
            logger.error(f"Failed to update profile: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Unexpected error updating profile for user_id {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update profile")
