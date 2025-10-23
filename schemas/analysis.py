# schemas\analysis.py

from pydantic import BaseModel

class AnalysisOut(BaseModel):
    analysis_id: str
    detected_item: str | None = None
    material_type: str | None = None
    suggested_title: str | None = None
