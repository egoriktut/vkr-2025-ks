from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import router as auth_router
from app.api.analyze import router as analyze_router
from app.api.user import router as user_router

from app.db.db_operations import get_user
from app.db.dependencies import get_db

router = APIRouter()

@router.get("/")
async def root(db: Session = Depends(get_db)):
    user = get_user(db, 1)
    if not user:
        return {"message": "User not found"}
    return user
router.include_router(auth_router, prefix="/auth")
router.include_router(analyze_router, prefix="/analyze")
router.include_router(user_router, prefix="/user")