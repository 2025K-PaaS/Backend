# routers/analysis.py

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.orm import Session
from core.deps import get_db, get_current_user
from services.analysis_service import call_ai_and_save
from schemas.analysis import AnalysisOut

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.post("/image", response_model=AnalysisOut)
def analyze_image(
    image: UploadFile = File(...),
    username: str = Form(..., min_length=3, max_length=50),
    db: Session = Depends(get_db),
    _user = Depends(get_current_user),   # 로그인 필요
):
    try:
        anal = call_ai_and_save(db, username=username, file=image)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return AnalysisOut(
        analysis_id=anal.ai_analysis_id,
        detected_item=anal.detected_item,
        material_type=anal.material_type,
        suggested_title=anal.suggested_title,
    )
