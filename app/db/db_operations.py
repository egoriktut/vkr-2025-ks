from db.models import User
from sqlalchemy.orm import Session


def get_user(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()
