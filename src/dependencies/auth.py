import logging
from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_jwt_auth_manager
from src.database.session_sqlite import get_db
from src.database import UserGroupModel
from src.dependencies.accounts import get_user_repository
from src.exceptions.security import TokenExpiredError, InvalidTokenError
from src.repositories.accounts.accounts import UserRepository
from src.security.interfaces import JWTAuthManagerInterface
from src.security.permissions import GROUP_PERMISSIONS

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/accounts/login")

logger = logging.getLogger(__name__)

async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db),
        jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
        user_repository: UserRepository = Depends(get_user_repository)
):
    try:
        payload = jwt_manager.decode_access_token(token)

        user_id = payload.get("user_id")
        group_id = payload.get("group_id")

        logger.info(f"Decoded token: user_id={user_id}, group_id={group_id}")

        if not user_id or not group_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token."
            )

        user = await user_repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        stmt = select(UserGroupModel).where(UserGroupModel.id == group_id)
        result = await db.execute(stmt)
        group = result.scalars().first()

        if not group:
            logger.error(f"Group not found for group_id={group_id}")
            raise HTTPException(status_code=401, detail="Group not found")

        return {
            "user_id": user_id,
            "group": group.name,
            "is_active": user.is_active
        }
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail="Token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {str(e)}")


def require_permissions(
    required_permissions: list[str]
):
    required_permissions = required_permissions or []

    async def check_permissions(
        current_user: dict = Depends(get_current_user),
    ) -> bool:
        logger.debug(f"Checking permissions for user_id: {current_user['user_id']}, required: {required_permissions}")
        if not current_user["is_active"]:
            logger.warning(f"User {current_user['user_id']} is not active")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is not active."
            )

        user_permissions = GROUP_PERMISSIONS.get(current_user["group"], [])
        logger.info(f"User permissions: {user_permissions}")
        logger.info(f"Required permissions: {required_permissions}")
        logger.info(f"User group: {current_user['group']}")

        if set(required_permissions).difference(set(user_permissions)):
            logger.warning(f"User {current_user['user_id']} lacks required permissions: {set(required_permissions).difference(set(user_permissions))}")
            raise HTTPException(status_code=403, detail="User lacks required permissions")

        return True
    return check_permissions
