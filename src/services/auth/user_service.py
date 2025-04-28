from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import UserModel
from src.repositories.accounts import UserRepository
from src.services.base import BaseService


class UserService(BaseService):
    def __init__(
            self,
            db: AsyncSession,
            user_repository: UserRepository
    ):
        self.user_repository = user_repository
        super().__init__(db)

    async def activate_user_account(self, user: UserModel) -> None:
        if user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already active."
            )

        user.is_active = True
        self.db.add(user)
        await self.db.commit()
