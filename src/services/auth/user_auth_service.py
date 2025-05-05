import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import RefreshTokenModel
from src.repositories.accounts.accounts import UserRepository, RefreshTokenRepository
from src.schemas.accounts import MessageSchema
from src.security.interfaces import JWTAuthManagerInterface
from src.services.base import BaseService
from src.services.validation.user_validation_service import UserValidationService


logger = logging.getLogger(__name__)


class UserAuthService(BaseService):
    def __init__(
            self,
            user_repository: UserRepository,
            jwt_manager: JWTAuthManagerInterface,
            db: AsyncSession,
            user_validation_service: UserValidationService,
            refresh_token_rep = RefreshTokenRepository,
    ):
        super().__init__(db)
        self.user_repository = user_repository
        self.jwt_manager = jwt_manager
        self.user_validation_service = user_validation_service
        self.refresh_token_rep = refresh_token_rep

    async def login_user(self, email: str, password: str):
        try:
            user = await (
                self.user_validation_service.validate_user_credentials(
                    email, password
                )
            )
            access_token = self.jwt_manager.create_access_token(
                data={"user_id": user.id, "group_id": user.group_id}
            )
            refresh_token = self.jwt_manager.create_refresh_token(
                data={"user_id": user.id, "group_id": user.group_id}
            )
            refresh_token_instance = RefreshTokenModel.create(
                user_id=user.id,
                token=refresh_token,
                days_valid=7
            )
            self.db.add(refresh_token_instance)
            await self.db.commit()

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }

        except HTTPException:
            await self.db.rollback()
            raise

        except Exception as e:
            logger.error(f"Error during login: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred during login."
            )

    async def refresh_access_token(self, refresh_token: str) -> dict:
        try:
            try:
                payload = self.jwt_manager.decode_refresh_token(refresh_token)
                if not payload or "user_id" not in payload:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid refresh token."
                    )
                user_id = payload["user_id"]
            except Exception as e:
                error_msg = str(e).lower()
                logger.warning(f"Token validation error: {error_msg}")
                if "expired" in error_msg:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Token has expired."
                    )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid refresh token."
                )

            token_record = await self.refresh_token_rep.get_refresh_token(token=refresh_token)
            if not token_record:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token not found."
                )
            if token_record.user_id != user_id:
                logger.warning(f"Token user ID mismatch: {token_record.user_id} != {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token."
                )

            user = await self.user_repository.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found."
                )

            new_access_token = self.jwt_manager.create_access_token(
                data={"user_id": user.id, "group_id": user.group_id}
            )
            return {"access_token": new_access_token}

        except HTTPException:
            await self.db.rollback()
            raise

        except Exception as e:
            logger.error(f"Error during token refresh: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred during refresh."
            )

    async def logout_user(self, refresh_token: str) -> MessageSchema:
        """
        Log out a user by validating and removing their JWT refresh token from the database.

        Args:
            refresh_token (str): The JWT refresh token to invalidate.

        Returns:
            MessageSchema: A response indicating successful logout.

        Raises:
            HTTPException: If the refresh token is invalid, not found, expired, or an error occurs.
        """
        logger.info(f"Attempting to log out user with refresh token: {refresh_token[:10]}...")

        try:
            try:
                payload = self.jwt_manager.decode_refresh_token(refresh_token)
                if not payload or "user_id" not in payload:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid refresh token."
                    )
            except Exception as e:
                error_msg = str(e).lower()
                logger.warning(f"Token validation error during logout: {error_msg}")
                if "expired" in error_msg:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Token has expired."
                    )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid refresh token."
                )

            async with self.db.begin():
                token_record = await self.refresh_token_rep.get_refresh_token(token=refresh_token)

                if not token_record:
                    logger.warning(f"Refresh token not found in database: {refresh_token[:10]}...")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Refresh token not found."
                    )
                await self.db.delete(token_record)
                logger.info(f"Refresh token deleted successfully: {refresh_token[:10]}...")

            return MessageSchema(message="Logout successful.")

        except HTTPException:
            raise

        except Exception as e:
            logger.error(f"Unexpected error during logout: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred during logout."
            )
