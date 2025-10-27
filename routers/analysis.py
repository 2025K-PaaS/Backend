# routers/analysis.py
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from core.deps import get_db, get_current_user
from services.analysis_service import call_ai_and_save
from schemas.analysis import AnalysisCreateOut

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.post("/image", response_model=AnalysisCreateOut)
def analyze_image(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    try:
        anal = call_ai_and_save(db=db, username=current_user.username, file=image)
        extracted = {
            "item_name": getattr(anal, "detected_item", None),
            "material_type": getattr(anal, "material_type", None),
            "title_suggested": getattr(anal, "suggested_title", None),
        }
        return AnalysisCreateOut(
            analysis_id=anal.ai_analysis_id,          
            extracted=extracted,
            image_url=getattr(anal, "image_path", None),
            status="pending",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
