from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.api import router as auth_router
from app.api.analyze import router as analyze_router
from app.user.api import router as user_router

from app.db.dependencies import get_db

router = APIRouter()

@router.get("/")
async def ping(db: Session = Depends(get_db)):
    if db:
        return "db successful connected"
    return "something went wrong"

router.include_router(auth_router, prefix="/auth")
router.include_router(analyze_router, prefix="/analyze")
router.include_router(user_router, prefix="/user")