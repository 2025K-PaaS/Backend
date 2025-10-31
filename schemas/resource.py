# schemas/resource.py
from enum import Enum
from typing import Optional, List, Union

from pydantic import BaseModel, Field


class ResourceStatus(str, Enum):
    registered = "registered"
    matched = "matched"
    completed = "completed"


class ResourceCreateIn(BaseModel):
    analysis_id: str
    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=300)
    amount: Optional[Union[str, float, int]] = None
    value: Optional[int] = None
    item_name: Optional[str] = None
    material_type: Optional[str] = None
    matched_request_id: Optional[str] = None
    item_type: Optional[str] = None 
    image_path: Optional[str] = None


class MatchedRequest(BaseModel):
    request_id: str
    wanted_item: str
    item_type: Optional[str] = None 
    material_type: Optional[str] = None
    desired_amount: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    username: Optional[str] = None
    
class ResourceCreateOut(BaseModel):
    resource_id: str
    status: ResourceStatus | str
    message: str
    matched_requests: List[MatchedRequest] = Field(default_factory=list)

class ResourceRow(BaseModel):
    resource_id: str
    title: str
    item_name: Optional[str] = None 
    username: Optional[str] = None  
    item_type: Optional[str] = None 
    material_type: Optional[str] = None
    amount: float
    value: int
    status: ResourceStatus | str
    image_url: Optional[str] = None
    description: Optional[str] = None


class ResourceListOut(BaseModel):
    resources: List[ResourceRow]
    total: int