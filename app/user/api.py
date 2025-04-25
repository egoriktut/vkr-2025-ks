from api.utils import get_current_token
from db.dependencies import get_db
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from user.schemas import UserBase, UserChangeCredentials
from user.services import UserService

router = APIRouter()


@router.get("/account", status_code=status.HTTP_200_OK, response_model=UserBase)
def get_me(token: str = Depends(get_current_token), db: Session = Depends(get_db)):
    return UserService.get_user_by_token(db, token)


# history


@router.put("/account", status_code=status.HTTP_200_OK, response_model=UserBase)
def update_my_credentials(
    credentials: UserChangeCredentials,
    token: str = Depends(get_current_token),
    db: Session = Depends(get_db),
):
    return UserService.change_credentials(db, token, credentials)
