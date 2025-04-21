from src.database import UserGroupEnum


GROUP_PERMISSIONS = {
    UserGroupEnum.ADMIN: ["read", "write", "delete", "manage_users"],
    UserGroupEnum.USER: ["read"],
    UserGroupEnum.MODERATOR: ["read", "write"],
}