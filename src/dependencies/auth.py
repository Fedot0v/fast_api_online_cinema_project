from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_jwt_auth_manager
from src.database import get_db, UserGroupModel, UserProfileModel
from src.database.models.movies import MovieCommentModel, MovieFavoriteModel
from src.dependencies.accounts import get_user_repository
from src.exceptions.security import TokenExpiredError, InvalidTokenError
from src.repositories.accounts.accounts import UserRepository
from src.security.interfaces import JWTAuthManagerInterface
from src.security.permissions import GROUP_PERMISSIONS


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/accounts/login")


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

        if not user_id or not group_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token."
            )

        user = await user_repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

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

        return {
            "user_id": user_id,
            "group": group,
            "is_active": user.is_active
        }
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail="Token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {str(e)}")


def require_permissions(
        required_permissions: list[str],
        require_owner: bool = False,
        owner_id_field: Optional[str] = None
):
    required_permissions = required_permissions or []

    async def check_permissions(
            current_user: dict = Depends(get_current_user),
            obj: Optional[
                MovieCommentModel | MovieFavoriteModel | UserProfileModel
            ] = None,
            user_id: Optional[int] = None,
    ):
        if not current_user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is not active."
            )

        user_permissions = GROUP_PERMISSIONS.get(current_user["group"].name, [])

        is_owner = False
        if require_owner and owner_id_field and user_id is not None:
            is_owner = user_id == current_user["user_id"]
        elif require_owner and obj is not None:
            is_owner = obj.user_id == current_user["user_id"]

        if not is_owner and set(required_permissions).difference(set(user_permissions)):
            raise HTTPException(status_code=403, detail="User lacks required permissions")

        if require_owner:
            if owner_id_field:
                if user_id != current_user["user_id"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="User does not have permission to modify this object."
                    )
            else:
                if obj is None:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Missing object for ownership check."
                    )
                if obj.user_id != current_user["user_id"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="User is not the owner of the object"
                    )
        return True
    return check_permissions
