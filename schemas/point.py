# schemas/point.py
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class PointBalanceOut(BaseModel):
    balance: int = 0    # 현재 보유 포인트(사용한 것 제외)
    lifetime_earned: int   # 누적 획득 포인트 (사용한 것 포함)
    level: int
    title: str

class PointHistoryItem(BaseModel):
    id: int
    delta: int
    reason: str
    ref_type: Optional[str] = None
    ref_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PointHistoryOut(BaseModel):
    items: List[PointHistoryItem]
    next_before_id: Optional[int] = None

class GrantPointsIn(BaseModel):
    user_id: int
    amount: int = Field(..., ge=-1_000_000, le=1_000_000)
    reason: str = "admin_grant"
    idempotency_key: Optional[str] = None
