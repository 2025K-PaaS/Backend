# schemas/point.py

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class PointBalanceOut(BaseModel):
    balance: int = 0

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
