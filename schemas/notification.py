# schemas/notification.py
from typing import Optional, List, Literal, Dict, Any, Union
from pydantic import BaseModel, Field

NumberLike = Union[int, float, str]

class ResourceBrief(BaseModel):
    resource_id: str
    title: Optional[str] = None
    item_name: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[str] = None
    value: Optional[int] = None
    username: Optional[str] = None
    item_type: Optional[str] = None 
    material_type: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = None
    

class RequestBrief(BaseModel):
    request_id: str
    title: Optional[str] = None
    item_name: Optional[str] = None
    amount: Optional[str] = None
    value: Optional[int] = None
    description: Optional[str] = None
    username: Optional[str] = None
    item_type: Optional[str] = None 
    material_type: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = None
    is_auto_written: bool = False   

    class Config:
        orm_mode = True
        exclude_defaults = False

class MatchProposalItem(BaseModel):
    state: str             
    role: Literal["supplier", "requester"]  
    resource: Optional[ResourceBrief] = None
    request: Optional[RequestBrief] = None

class MatchProposalsOut(BaseModel):
    proposals: List[MatchProposalItem]
    total: int


class ManualMatchIn(BaseModel):
    resource_id: str = Field(..., description="매칭할 자원 ID")
    amount: NumberLike = Field(..., description="요청 수량(문자열/숫자 허용)")

class ManualMatchResponse(BaseModel):
    manual: Dict[str, Any]