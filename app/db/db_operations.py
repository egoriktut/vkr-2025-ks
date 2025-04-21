from sqlalchemy.orm import Session
from app.db.models import User

def get_user(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()
