from fastapi import HTTPException, status

from src.repositories.accounts import UserRepository


class UserValidationService:
    def __init__(
            self,
            user_repository: UserRepository
    ):
        self.user_repository = user_repository

    async def validate_email_uniqueness(self, email: str):
        existing_user = await self.user_repository.get_user_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A user with this email {email} already exists."
            )

    async def validate_user_credentials(self, email: str, password: str):
        user = await self.user_repository.get_user_by_email(email)
        if not user or not user.verify_password(password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not active."
            )
        return user
