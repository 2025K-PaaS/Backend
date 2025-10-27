# models/user.py

import enum
from sqlalchemy import String, Integer, DateTime, func, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base

class UserRole(str, enum.Enum):
    user = "user"     

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("nickname", name="uq_users_nickname"),
        UniqueConstraint("phone", name="uq_users_phone"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)  # 아이디
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)  
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.user, nullable=False)

    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    point_wallet = relationship("PointWallet", uselist=False, back_populates="user")
    point_ledger = relationship("PointLedger", back_populates="user")
    
    requests = relationship("Request", back_populates="user")
