from sqlalchemy.ext.asyncio import AsyncSession


class BaseAccountRepository:
    def __init__(
            self,
            db: AsyncSession,
    ):
        self.db = db
