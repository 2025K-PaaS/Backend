# routers/analysis.py
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from core.utils import make_public_url 
from core.deps import get_db, get_current_user
from services.analysis_service import call_ai_and_save, get_analysis_by_id
from schemas.analysis import AnalysisCreateOut

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.post("/image", response_model=AnalysisCreateOut)
def analyze_image_route(
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
        image_url = make_public_url(getattr(anal, "image_path", None))

        return AnalysisCreateOut(
            analysis_id=anal.ai_analysis_id,
            extracted=extracted,
            image_url=image_url,
            status="pending",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 분석내용 재조회 API
@router.get("/{analysis_id}", response_model=AnalysisCreateOut)
def get_analysis_route(
    analysis_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    anal = get_analysis_by_id(db=db, username=current_user.username, analysis_id=analysis_id)
    if not anal:
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")

    extracted = {
        "item_name": getattr(anal, "detected_item", None),
        "material_type": getattr(anal, "material_type", None),
        "title_suggested": getattr(anal, "suggested_title", None),
    }

    image_url = make_public_url(getattr(anal, "image_path", None))

    return AnalysisCreateOut(
        analysis_id=anal.ai_analysis_id,
        extracted=extracted,
        image_url=image_url,
        status=getattr(anal, "status", "pending"),
    )
