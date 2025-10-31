# services/auth_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.user import User
from repositories.user_repo import UserRepository
from core.security import get_password_hash, verify_password, create_access_token
from schemas.auth import SignUpIn
from services import point_service 

class AuthService:
    def __init__(self):
        self.users = UserRepository()

    # 회원가입
    def signup(self, db: Session, body: SignUpIn) -> User:
        if self.users.get_by_username(db, body.username):
            raise HTTPException(status_code=409, detail="이미 사용 중인 아이디입니다.")
        if body.nickname and self.users.get_by_nickname(db, body.nickname):
            raise HTTPException(status_code=409, detail="이미 사용 중인 닉네임입니다.")
        if body.phone and self.users.get_by_phone(db, body.phone):
            raise HTTPException(status_code=409, detail="이미 등록된 전화번호입니다.")

        user = User(
            username=body.username,
            hashed_password=get_password_hash(body.password),
            name=body.name,
            phone=body.phone,
            nickname=body.nickname,
            address=body.address,
        )
        created_user = self.users.create(db, user)

        try:
            point_service.award(
                db=db,
                user_id=created_user.id,
                amount=500,
                ref_type="system",
                ref_id="signup_bonus",
                item_title="회원가입 축하 포인트",
                item_amount=1,
                idempotency_key=f"signup-{created_user.id}",
            )
            db.commit()
            print(f"[포인트 지급] {created_user.username} 가입 축하 +500P")
        except Exception as e:
            db.rollback()
            print(f"[경고] 포인트 지급 실패: {e}")

        return created_user
    

    # 로그인
    def authenticate(self, db: Session, username: str, password: str) -> User:
        user = self.users.get_by_username(db, username)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="아이디 또는 비밀번호가 올바르지 않습니다.")
        return user

    # 토큰 발급
    def issue_token(self, user_id: int) -> str:
        return create_access_token(user_id)

    def get_user_by_id(self, db: Session, user_id: int) -> User | None:
        return self.users.get_by_id(db, user_id)