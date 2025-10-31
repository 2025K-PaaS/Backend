# models/point.py
from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime, func, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from db.base import Base

class PointWallet(Base):
    __tablename__ = "point_wallets"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    balance = Column(Integer, nullable=False, default=0)
    user = relationship("User", back_populates="point_wallet", lazy="joined")


class PointLedger(Base):
    __tablename__ = "point_ledger"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    delta = Column(Integer, nullable=False)
    reason = Column(String(50), nullable=True)       
    ref_type = Column(String(50), nullable=True)
    ref_id = Column(String(100), nullable=True)
    item_title = Column(String(100), nullable=True)
    item_amount = Column(Float, nullable=True)
    idempotency_key = Column(String(64), nullable=True, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="point_ledger")

    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_point_ledger_idemp"),
        Index("ix_point_ledger_user_id", "user_id"),
    )