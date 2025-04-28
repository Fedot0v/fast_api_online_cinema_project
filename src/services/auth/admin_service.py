import logging

from fastapi import HTTPException, status
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import UserGroupModel, ActivationTokenModel
from src.repositories.accounts import UserRepository
from src.services.base import BaseService


logger = logging.getLogger(__name__)


class AdminService(BaseService):
    def __init__(
            self,
            db: AsyncSession,
            user_repository: UserRepository,
    ):
        super().__init__(db)
        self.user_repository = user_repository

    async def change_user_group(
            self,
            user_id: int,
            new_group_id: int,
            admin_user_id: int
    ) -> None:
        logger.info(f"Admin {admin_user_id} attempting to change group for user {user_id}")
        try:
            async with self.db.begin():
                user = await self.user_repository.get_user_by_id(user_id)
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found."
                    )
                group = await self.db.get(UserGroupModel, new_group_id)
                if not group:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid group id."
                    )
                user.group_id = new_group_id
                await self.db.commit()
                logger.info(f"User {user_id} group changed to {group.name}")
        except HTTPException as e:
            await self.db.rollback()
            raise e
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error during group change: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="An error occurred during group change.")

    async def manually_activate_user(
            self,
            user_id: int,
            admin_user_id: int
    ) -> None:
        logger.info(f"Admin {admin_user_id} attempting to manually activate user {user_id}")
        try:
            async with self.db.begin():
                user = await self.user_repository.get_user_by_id(user_id)
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found."
                    )
                if user.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="User is already active."
                    )
                user.is_active = True
                stmt = delete(ActivationTokenModel).where(
                    ActivationTokenModel.user_id == user_id
                )
                await self.db.execute(stmt)
                await self.db.commit()
                logger.info(f"Account activated for user {user_id} by admin {admin_user_id}")
        except HTTPException as e:
            await self.db.rollback()
            raise e
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error during manual activation: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="An error occurred during manual activation")
