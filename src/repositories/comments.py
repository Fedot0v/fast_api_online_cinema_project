from typing import Optional, Sequence

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database import UserModel
from src.database.models.movies import MovieCommentModel
from src.repositories.base import BaseRepository


class CommentsRepository(BaseRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def create_comment(
            self,
            user_id: int,
            movie_id: int,
            content: str,
            # parent_comment_id: Optional[int] = None
    ) -> MovieCommentModel:
        # if parent_comment_id:
        #     parent = await self.repo.get_comment_by_id(parent_comment_id)
        #     if not parent:
        #         raise ValueError("Parent comment does not exist")
        #
        #     if parent.parent_comment_id:
        #         grandparent = await self.repo.get_comment_by_id(parent.parent_comment_id)
        #         if grandparent and grandparent.parent_comment_id:
        #             raise ValueError("Maximum depth of replies is 2") #TODO service layer

        comment = MovieCommentModel(
            user_id=user_id,
            movie_id=movie_id,
            content=content
        )
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    async def get_comment_by_id(self, comment_id: int) -> Optional[MovieCommentModel]:
        stmt = (
            select(MovieCommentModel)
            .where(MovieCommentModel.id == comment_id)
            .options(
                joinedload(MovieCommentModel.user)
                .joinedload(UserModel.profile)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_comments(
        self,
        movie_id: int,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Sequence[MovieCommentModel]:
        stmt = (
            select(MovieCommentModel)
            .where(MovieCommentModel.movie_id == movie_id)
            .options(
            joinedload(MovieCommentModel.user)
            .joinedload(UserModel.profile)
            )
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def delete_comment(self, comment_id: int) -> None:
        stmt = delete(MovieCommentModel).where(MovieCommentModel.id == comment_id)
        await self.db.execute(stmt)
        await self.db.commit()