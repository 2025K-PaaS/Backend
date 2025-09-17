# routers/users.py

from fastapi import APIRouter, Depends
from core.deps import get_current_user
from schemas.user import UserOut

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserOut)
def get_me(user = Depends(get_current_user)):
    return user
