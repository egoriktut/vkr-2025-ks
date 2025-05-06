from datetime import datetime
from typing import Any

from db.database import Base, engine
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    created_at = Column(DateTime(timezone=True), default=datetime.now())
    verification_code = Column(String)
    activated = Column(Boolean, default=False)
    token = Column(String)

    @property
    def as_dict(self) -> dict[str, Any]:
        return self.__dict__


class TaskHistory(Base):
    __tablename__ = "task_history"

    id = Column(Integer, primary_key=True, index=True)
    ids = Column(String, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    url = Column(String)
    description = Column(Text)
    status = Column(String)
    result = Column(String)
    created_at = Column(DateTime(timezone=True), default=datetime.now())
    completed_at = Column(DateTime(timezone=True))


Base.metadata.create_all(bind=engine)
