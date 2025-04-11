from fastapi import APIRouter


router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("/register/")
async def register():
    pass
