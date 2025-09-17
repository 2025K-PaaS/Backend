# schemas/user.py
from pydantic import BaseModel
from models.user import UserRole

class UserOut(BaseModel):
    id: int
    username: str
    name: str
    phone: str | None
    nickname: str | None
    role: UserRole

    class Config:
        from_attributes = True  # SQLAlchemy -> Pydantic v2
