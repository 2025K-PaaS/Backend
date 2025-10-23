# services/auth_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.user import User
from repositories.user_repo import UserRepository
from core.security import get_password_hash, verify_password, create_access_token
from schemas.auth import SignUpIn

class AuthService:
    def __init__(self):
        self.users = UserRepository()

    # 회원가입
    def signup(self, db: Session, body: SignUpIn) -> User:
        if self.users.get_by_username(db, body.username):
            raise HTTPException(status_code=409, detail="Username already exists")
        if body.nickname and self.users.get_by_nickname(db, body.nickname):
            raise HTTPException(status_code=409, detail="Nickname already exists")
        if body.phone and self.users.get_by_phone(db, body.phone):
            raise HTTPException(status_code=409, detail="Phone already exists")

        user = User(
            username=body.username,
            hashed_password=get_password_hash(body.password),
            name=body.name,
            phone=body.phone,
            nickname=body.nickname,
        )
        return self.users.create(db, user)

    # 로그인
    def authenticate(self, db: Session, username: str, password: str) -> User:
        user = self.users.get_by_username(db, username)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return user

    # 토큰 발급
    def issue_token(self, user_id: int) -> str:
        return create_access_token(user_id)

    def get_user_by_id(self, db: Session, user_id: int) -> User | None:
        return self.users.get_by_id(db, user_id)
