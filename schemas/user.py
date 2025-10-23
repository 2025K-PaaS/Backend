# schemas/user.py

from pydantic import BaseModel, ConfigDict
from models.user import UserRole

class UserOut(BaseModel):
    id: int
    username: str
    name: str
    phone: str | None
    nickname: str | None
    role: UserRole
    model_config = ConfigDict(from_attributes=True)  # Pydantic v2
