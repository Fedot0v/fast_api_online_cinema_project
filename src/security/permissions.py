from src.database import UserGroupEnum


GROUP_PERMISSIONS = {
    UserGroupEnum.ADMIN: [
        "read",
        "write",
        "delete",
        "manage_users",
        "comment",
        "favorite",
        "like"
    ],
    UserGroupEnum.USER: [
        "read",
        "comment",
        "favorite",
        "like",
        "cart"
    ],
    UserGroupEnum.MODERATOR: [
        "read",
        "write",
        "comment",
        "favorite",
        "like",
        "cart"
    ],
}
