from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.deps import get_db, get_current_user
from services.resource_service import create_from_ai_analysis, list_by_username
from schemas.resource import ResourceCreateIn, ResourceCreateOut, MatchedRequest, ResourceListOut, ResourceRow

router = APIRouter(prefix="/resources", tags=["resources"])

@router.post("", response_model=ResourceCreateOut)
def create_resource(
    payload: ResourceCreateIn,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    try:
        res, matches = create_from_ai_analysis(
            db=db,
            user_id=current_user.id,
            ai_analysis_id=payload.analysis_id,
            title=payload.title,
            description=payload.description,
            amount=payload.amount,
            unit=payload.unit,
            value=payload.value,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ResourceCreateOut(
        resource_id=res.id,
        status=res.status,
        message="자원이 성공적으로 등록되었습니다.",
        matched_requests=[
            MatchedRequest(
                request_id=m.id,
                wanted_item=m.wanted_item,
                material_type=m.material_type,
                desired_amount=m.desired_amount,
                unit=m.unit,
            ) for m in matches
        ],
    )

@router.get("/user/{username}", response_model=ResourceListOut)
def list_resources(username: str, db: Session = Depends(get_db)):
    rows, total = list_by_username(db, username)
    return ResourceListOut(
        resources=[
            ResourceRow(
                resource_id=r.id,
                title=r.title,
                material_type=r.material_type,
                amount=r.amount,
                unit=r.unit,
                value=r.value,
                status=r.status,
            ) for r in rows
        ],
        total=total,
    )
