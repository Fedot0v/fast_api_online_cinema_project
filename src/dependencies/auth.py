from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_jwt_auth_manager
from src.database import get_db, UserGroupModel, UserGroupEnum
from src.dependencies.accounts import get_user_repository
from src.repositories.accounts import UserRepository
from src.security.interfaces import JWTAuthManagerInterface
from src.security.permissions import GROUP_PERMISSIONS

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/accounts/login")

async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db),
        jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager)
):
    try:
        payload = jwt_manager.decode_access_token(token)

        user_id = payload.get("user_id")
        group_id = payload.get("group_id")

        if not user_id or not group_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token."
            )

        stmt = select(UserGroupModel).where(
            UserGroupModel.id == group_id
        )
        result = await db.execute(stmt)
        group = result.scalar_one_or_none()

        if not group:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Group not found."
            )

        return {"user_id": user_id, "group": group}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {str(e)}")


def require_permissions(required_permissions: list[str]):
    async def check_permissions(
            current_user: dict = Depends(get_current_user)
    ):
        group_name = current_user["group"].name
        group_permission = GROUP_PERMISSIONS.get(UserGroupEnum(group_name), [])
        if not all(perm in group_permission for perm in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to perform this action."
            )
        return current_user
    return check_permissions
