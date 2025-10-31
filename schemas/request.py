# schemas/request.py
from pydantic import BaseModel
from typing import Optional, List

class RequestCreateIn(BaseModel):
    title: Optional[str] = None  
    item_name: str
    amount: str
    description: str
    item_type: Optional[str] = None
    material_type: Optional[str] = None

class RequestOut(BaseModel):
    request_id: str         
    status: str
    message: str
    image_url: Optional[str] = None 

class RequestRow(BaseModel):
    request_id: str  
    title: Optional[str] = None      
    wanted_item: str
    item_type: Optional[str] = None  
    material_type: Optional[str] = None
    desired_amount: float   
    description: Optional[str] = None
    image_url: Optional[str] = None
    status: str
    is_auto_written: bool = False   

    class Config:
        orm_mode = True
        exclude_defaults = False


class RequestListOut(BaseModel):
    requests: list[RequestRow]
    total: int

class RequestListWithAddressOut(BaseModel):
    username: str
    address: Optional[str] = None
    phone: Optional[str] = None
    requests: List[RequestRow]
    total: int

class RequestDetailOut(BaseModel):
    request_id: str
    title: Optional[str] = None
    wanted_item: Optional[str] = None
    item_type: Optional[str] = None 
    material_type: Optional[str] = None
    desired_amount: Optional[float] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    username: Optional[str] = None
    status: str = "pending"
    is_auto_written: bool = False

    class Config:
        orm_mode = True
        exclude_defaults = False
    