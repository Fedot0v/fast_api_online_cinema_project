import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.routes import accounts, cart, directors, genres, movies, orders, stars, certifications
from src.database import init_db, close_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application")
    await init_db()
    yield
    await close_db()
    logger.info("Application shutdown")

app = FastAPI(lifespan=lifespan)

api_version_prefix = "/api/v1"
app.include_router(accounts.router, prefix=f"{api_version_prefix}")
app.include_router(cart.router, prefix=f"{api_version_prefix}")
app.include_router(directors.router, prefix=f"{api_version_prefix}")
app.include_router(genres.router, prefix=f"{api_version_prefix}")
app.include_router(movies.router, prefix=f"{api_version_prefix}")
app.include_router(orders.router, prefix=f"{api_version_prefix}")
app.include_router(stars.router, prefix=f"{api_version_prefix}")
app.include_router(certifications.router, prefix=f"{api_version_prefix}")

logger.info("FastAPI application initialized")

logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)