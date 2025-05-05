from typing import List, Optional

from fastapi import HTTPException

from src.database import UserGroupEnum, UserGroupModel
from src.database.models.notifications import NotificationType
from src.repositories.movies.comments import CommentsRepository
from src.repositories.notifications import NotificationRepository
from src.schemas.movies import CommentResponseSchema, CommentCreateSchema, CommentReplySchema
from src.security.permissions import GROUP_PERMISSIONS


class CommentsService:
    def __init__(
            self,
            comment_repository: CommentsRepository,
            notification_repository: NotificationRepository
    ):
        self.comment_repository = comment_repository
        self.notification_repository = notification_repository


    async def _validate_nesting_level(
            self,
            parent_comment_id: Optional[int]
    ) -> None:
        if parent_comment_id:
            parent = await self.comment_repository.get_comment_by_id(parent_comment_id)
            if not parent:
                raise ValueError("Parent comment not found")

            if parent.parent_comment_id:
                grandparent = await self.comment_repository.get_comment_by_id(parent.parent_comment_id)
                if grandparent and grandparent.parent_comment_id:
                    raise ValueError("Maximum nesting level for replies is 2")

    async def create_comment(
            self,
            movie_id: int,
            user_id: int,
            comment_data: CommentCreateSchema,
    ) -> CommentResponseSchema:
        await self._validate_nesting_level(comment_data.parent_comment_id)

        comment = await self.comment_repository.create_comment(
            movie_id=movie_id,
            user_id=user_id,
            content=comment_data.content,
            parent_comment_id=comment_data.parent_comment_id
        )

        if comment_data.parent_comment_id:
            parent_comment = await self.comment_repository.get_comment_by_id(comment_data.parent_comment_id)
            if parent_comment and parent_comment.user_id != user_id:
                await self.notification_repository.create_notification(
                    user_id=parent_comment.user_id,
                    notification_type=NotificationType.COMMENT_REPLY,
                    trigger_user_id=user_id,
                    comment_id=comment.id
                )

        replies = []
        if comment_data.parent_comment_id:
            replies = await self.comment_repository.get_replies_for_comment(comment.id)
            replies = [CommentReplySchema.model_validate(reply) for reply in replies]

        response = CommentResponseSchema(
            id=comment.id,
            movie_id=comment.movie_id,
            user_id=comment.user_id,
            content=comment.content,
            created_at=comment.created_at,
            replies=replies
        )

        return response

    async def get_movie_comments(
            self,
            movie_id: int
    ) -> List[CommentResponseSchema]:
        comments = await self.comment_repository.get_movie_comments(movie_id)
        response = []

        for comment in comments:
            replies = [
                CommentReplySchema.model_validate(reply)
                for reply in comment.replies
            ]
            comment_data = CommentResponseSchema.model_validate(comment)
            comment_data.replies = replies
            response.append(comment_data)

        return response

    async def delete_comment(
            self,
            movie_id: int,
            comment_id: int,
            user_id: int,
            user_group: UserGroupModel
    ) -> None:
        if movie_id <= 0 or comment_id <= 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid movie or comment id"
            )

        comment = await self.comment_repository.get_comment_by_id(comment_id)
        if not comment:
            raise HTTPException(
                status_code=404,
                detail="Comment not found"
            )
        if comment.movie_id != movie_id:
            raise HTTPException(
                status_code=400,
                detail="Comment does not belong to this movie"
            )

        try:
            group_enum = UserGroupEnum[user_group.name.upper()]
        except (AttributeError, KeyError):
            raise HTTPException(
                status_code=400,
                detail="Invalid user group"
            )

        is_owner = comment.user_id == user_id
        has_delete_permission = "delete" in GROUP_PERMISSIONS.get(
            group_enum,
            []
        )
        if not (is_owner or has_delete_permission):
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to delete this comment"
            )
        await self.comment_repository.delete_comment(comment_id)
