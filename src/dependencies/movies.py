from typing import TypeVar, Type

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.repositories.movies.certificates import CertificationRepository
from src.repositories.movies.comments import CommentsRepository
from src.repositories.movies.directors import DirectorRepository
from src.repositories.movies.favorites import FavoriteRepository
from src.repositories.movies.genres import GenreRepository
from src.repositories.movies.movies import MovieRepository
from src.repositories.movies.ratings import RatingsRepository
from src.repositories.movies.stars import StarRepository
from src.repositories.notifications import NotificationRepository
from src.services.movies.comments_service import CommentsService
from src.services.movies.director_service import DirectorService
from src.services.movies.favorites_service import FavoriteService
from src.services.movies.genre_service import GenreService
from src.services.movies.movie_service import MovieService
from src.services.movies.rating_service import RatingService
from src.services.movies.star_service import StarService


T = TypeVar("T")


def get_repository(repo_class: Type[T]):
    """
    Fabric for creating a repository instance.
    """

    def _get_repo(db: AsyncSession = Depends(get_db)) -> T:
        return repo_class(db)

    return _get_repo


def get_rating_service(
        movie_repo: MovieRepository = Depends(
            get_repository(MovieRepository)
        ),
        rating_repo: RatingsRepository = Depends(
            get_repository(RatingsRepository)
        )
) -> RatingService:
    return RatingService(
        movie_repository=movie_repo,
        ratings_repository=rating_repo
    )


def get_movie_service(
        movie_repo: MovieRepository = Depends(
            get_repository(MovieRepository)
        ),
        star_repo: StarRepository = Depends(get_repository(StarRepository)),
        director_repo: DirectorRepository = Depends(
            get_repository(DirectorRepository)
        ),
        certification_repo: CertificationRepository = Depends(
            get_repository(CertificationRepository)
        ),
        genre_repo: GenreRepository = Depends(
            get_repository(GenreRepository)
        ),
        ratings_repo: RatingsRepository = Depends(
            get_repository(RatingsRepository)
        )
) -> MovieService:
    return MovieService(
        movie_repository=movie_repo,
        star_repository=star_repo,
        director_repository=director_repo,
        certification_repository=certification_repo,
        genre_repository=genre_repo,
        ratings_repository=ratings_repo
    )


def get_comment_service(
        comment_repo: CommentsRepository = Depends(get_repository(CommentsRepository)),
        notification_repo: NotificationRepository = Depends(
            get_repository(NotificationRepository)
        )
) -> CommentsService:
    return CommentsService(comment_repo, notification_repo)


def get_director_service(
        director_repo: DirectorRepository = Depends(
            get_repository(DirectorRepository)
        )
) -> DirectorService:
    return DirectorService(director_repo)


def get_star_service(
        star_repo: StarRepository = Depends(get_repository(StarRepository))
) -> StarService:
    return StarService(star_repo)


def get_genre_service(
        genre_repo: GenreRepository = Depends(get_repository(GenreRepository))
) -> GenreService:
    return GenreService(genre_repo)


def get_favorite_service(
        movie_repo: MovieRepository = Depends(
            get_repository(MovieRepository)
        ),
        notification_repo: NotificationRepository = Depends(
            get_repository(NotificationRepository)
        ),
        favorite_repo: FavoriteRepository = Depends(
            get_repository(FavoriteRepository)
        )
) -> FavoriteService:
    return FavoriteService(
        favorite_repository=favorite_repo,
        notification_repository=notification_repo,
        movie_repository=movie_repo
    )
