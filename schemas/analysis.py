# schemas/analysis.py
from typing import Any, Dict, Optional
from pydantic import BaseModel

class AnalysisCreateOut(BaseModel):
    analysis_id: str
    extracted: Dict[str, Any] 
    image_url: Optional[str] = None
    status: str = "pending"
