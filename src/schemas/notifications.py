from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.database.models.notifications import NotificationType


class NotificationResponseSchema(BaseModel):
    id: int
    user_id: int
    type: NotificationType
    trigger_user_id: Optional[int] = None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }
