from fastapi import FastAPI


app = FastAPI(
    title="FastAPI Online Cinema Project",
    description="A FastAPI project for managing users and movies.",
)

api_version_prefix = "/api/v1"
