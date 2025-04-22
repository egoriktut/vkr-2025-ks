from datetime import datetime
from typing import Optional

from pydantic import BaseModel

class UserBase(BaseModel):
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    created_at: datetime

class UserHistory(BaseModel):
    pass

class UserChangeCredentials(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None