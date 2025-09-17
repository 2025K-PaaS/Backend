# repositories/user_repo.py

from sqlalchemy.orm import Session
from sqlalchemy import select
from models.user import User

class UserRepository:
    def get_by_id(self, db: Session, user_id: int) -> User | None:
        return db.get(User, user_id)

    def get_by_username(self, db: Session, username: str) -> User | None:
        return db.scalar(select(User).where(User.username == username))

    def get_by_nickname(self, db: Session, nickname: str) -> User | None:
        return db.scalar(select(User).where(User.nickname == nickname))

    def get_by_phone(self, db: Session, phone: str) -> User | None:
        return db.scalar(select(User).where(User.phone == phone))

    def create(self, db: Session, user: User) -> User:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
