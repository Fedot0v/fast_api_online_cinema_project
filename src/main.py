# src/main.py
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.routes import accounts
from src.database.session_sqlite import init_db, close_db

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
app.include_router(accounts.router, prefix=f"{api_version_prefix}/accounts", tags=["accounts"])

logger.info("FastAPI application initialized")