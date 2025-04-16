from fastapi import FastAPI
from src.routes import accounts


app = FastAPI(
    title="FastAPI Online Cinema Project",
    description="A FastAPI project for managing users and movies.",
)

api_version_prefix = "/api/v1"

app.include_router(
    accounts.router,
    prefix=api_version_prefix,
    tags=["accounts"]
)