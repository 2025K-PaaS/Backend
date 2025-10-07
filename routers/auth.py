# routers/auth.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from schemas.auth import SignUpIn, LoginIn, Token
from schemas.user import UserOut
from services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserOut)
def signup(
    body: SignUpIn,
    db: Session = Depends(get_db),
    svc: AuthService = Depends(AuthService),
):
    user = svc.signup(db, body)
    return user

@router.post("/login", response_model=Token)
def login(
    body: LoginIn,
    db: Session = Depends(get_db),
    svc: AuthService = Depends(AuthService), 
):
    user = svc.authenticate(db, body.username, body.password)
    token = svc.issue_token(user.id)
    return Token(access_token=token)

from core.deps import get_current_user
@router.get("/me", response_model=UserOut)
def me(user = Depends(get_current_user)):
    return user
