from src.database.models.accounts import (
    UserModel,
    UserGroupModel,
    UserGroupEnum,
    ActivationTokenModel,
    PasswordResetTokenModel,
    RefreshTokenModel,
    UserProfileModel
)

import os

if os.getenv("ENVIRONMENT") == "testing":
    from src.database.session_sqlite import (
        init_db,
        close_db,
        get_db_contextmanager,
        get_db,
        reset_sqlite_database
    )
else:
    from src.database.session_postgres import (
        init_db,
        close_db,
        get_db_contextmanager,
        get_db
    )

    def reset_sqlite_database():
        """Stub function for production environment"""
        raise NotImplementedError("This function is only available in testing environment")