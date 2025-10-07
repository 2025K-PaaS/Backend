# schemas/resource.py

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List

class ResourceStatus(str, Enum):
    registered = "registered"
    matched    = "matched"
    completed  = "completed"

class ResourceCreateIn(BaseModel):
    analysis_id: str
    title: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=300)
    amount: float = Field(ge=0)
    unit: str
    value: int = Field(ge=0)

class MatchedRequest(BaseModel):
    request_id: int
    wanted_item: str
    material_type: str | None = None
    desired_amount: float
    unit: str

class ResourceCreateOut(BaseModel):
    resource_id: int
    status: ResourceStatus | str 
    message: str
    matched_requests: List[MatchedRequest] = Field(default_factory=list)

class ResourceRow(BaseModel):
    resource_id: int
    title: str
    material_type: str | None = None
    amount: float
    unit: str
    value: int
    status: ResourceStatus | str

class ResourceListOut(BaseModel):
    resources: list[ResourceRow]
    total: int
