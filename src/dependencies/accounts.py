from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.config.dependencies import get_jwt_auth_manager
from src.security.interfaces import JWTAuthManagerInterface
from src.services.accounts import UserAccountService, ActivationTokenService


def get_user_service(
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager)
) -> UserAccountService:
    return UserAccountService(db, jwt_manager)


def get_activation_token_service(
        db: AsyncSession = Depends(get_db)
) -> ActivationTokenService:
    return ActivationTokenService(db)
