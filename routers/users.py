# routers/users.py

from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from core.deps import get_current_user, get_db
from schemas.user import UserOut

router = APIRouter(prefix="/users", tags=["users"])
