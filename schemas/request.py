# schemas/request.py

from pydantic import BaseModel, Field
from typing import Optional

class RequestCreateIn(BaseModel):
    wanted_item: str
    material_type: Optional[str] = None
    desired_amount: float = Field(ge=0)
    unit: str
    description: Optional[str] = None

class RequestOut(BaseModel):
    request_id: int
    status: str
    message: str

class RequestRow(BaseModel):
    request_id: int
    wanted_item: str
    material_type: str | None = None
    desired_amount: float
    unit: str
    status: str

class RequestListOut(BaseModel):
    requests: list[RequestRow]
    total: int
