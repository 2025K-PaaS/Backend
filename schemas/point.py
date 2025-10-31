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
    ref_type: Optional[str] = None
    ref_id: Optional[str] = None
    item_title: Optional[str] = None  
    item_amount: Optional[float] = None     
    created_at: datetime

    @property
    def safe_item_title(self) -> str:
        return self.item_title or "관리자 지급"
    
    class Config:
        from_attributes = True


class PointHistoryOut(BaseModel):
    items: List[PointHistoryItem]
    next_before_id: Optional[int] = None

class PointHistoryAllOut(PointBalanceOut):
    items: List[PointHistoryItem]
    
class GrantPointsIn(BaseModel):
    user_id: int
    amount: int = Field(..., ge=-1_000_000, le=1_000_000)
    idempotency_key: Optional[str] = None
