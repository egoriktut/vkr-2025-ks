from typing import List

from db.models import User
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from user.schemas import UserBase, UserChangeCredentials, UserHistory


class UserService:

    @staticmethod
    def get_user_by_token(db: Session, token: str) -> UserBase:
        user = db.query(User).filter_by(token=token).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"User not found"
            )

        return UserBase.model_validate(user.as_dict)

    @staticmethod
    def get_user_history(db: Session, token: str) -> List[UserHistory]:
        pass

    @staticmethod
    def change_credentials(
        db: Session, token: str, new_credentials: UserChangeCredentials
    ):
        user = db.query(User).filter_by(token=token).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"User not found"
            )

        user.first_name = new_credentials.first_name
        user.last_name = new_credentials.last_name

        db.commit()
        db.refresh(user)

        return UserBase.model_validate(user.as_dict)
