from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database.models.notifications import NotificationModel, NotificationType
from src.repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def create_notification(
            self,
            user_id: int,
            notification_type: NotificationType,
            trigger_user_id: Optional[int] = None,
            comment_id: Optional[int] = None,
    ) -> NotificationModel:
        notification = NotificationModel(
            user_id=user_id,
            type=notification_type,
            trigger_user_id=trigger_user_id,
            comment_id=comment_id
        )
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def get_user_notifications(self, user_id: int) -> Sequence[NotificationModel]:
        stmt = (
            select(NotificationModel)
            .where(NotificationModel.user_id == user_id)
            .options(
                joinedload(NotificationModel.user),
                joinedload(NotificationModel.trigger_user),
                joinedload(NotificationModel.comment)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
