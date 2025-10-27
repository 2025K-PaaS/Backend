# schemas/resource.py
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


class ResourceStatus(str, Enum):
    registered = "registered"
    matched = "matched"
    completed = "completed"


class ResourceCreateIn(BaseModel):
    analysis_id: str
    title: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=300)
    amount: Optional[float] = None
    unit: Optional[str] = None
    value: Optional[int] = None
    material_type: Optional[str] = None
    condition: Optional[str] = None
    tags: Optional[List[str]] = None


class MatchedRequest(BaseModel):
    request_id: str                
    wanted_item: str
    material_type: Optional[str] = None
    desired_amount: float
    unit: str


class ResourceCreateOut(BaseModel):
    resource_id: str               
    status: ResourceStatus | str
    message: str
    matched_requests: List[MatchedRequest] = Field(default_factory=list)


class ResourceRow(BaseModel):
    resource_id: str             
    title: str
    material_type: Optional[str] = None
    amount: float
    unit: str
    value: int
    status: ResourceStatus | str


class ResourceListOut(BaseModel):
    resources: List[ResourceRow]
    total: int
