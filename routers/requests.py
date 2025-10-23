# routers/requests.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.deps import get_db, get_current_user
from services.request_service import create, list_pending
from services.ai_client import create_request_on_ai           
from schemas.request import RequestCreateIn, RequestOut, RequestListOut, RequestRow

router = APIRouter(prefix="/requests", tags=["requests"])

@router.post("", response_model=RequestOut, status_code=201)
def create_request(
    payload: RequestCreateIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        ai_payload = {
            "item_name": payload.wanted_item,         
            "amount": int(payload.desired_amount),      
            "unit": payload.unit,                     
            "description": payload.description,     
            "username": current_user.username       
        }
        ai_resp = create_request_on_ai(ai_payload)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    req = create(db, created_by=current_user.id, **payload.dict())

    return RequestOut(
        request_id=req.id,
        status=ai_resp.get("status", "open"),
        message=ai_resp.get("message", "요청이 성공적으로 등록되었습니다."),
    )


@router.get("/pending", response_model=RequestListOut)
def get_pending_requests(
    material_type: str | None = Query(default=None),
    wanted_item: str | None = Query(default=None),
    status: str | None = Query(default=None),  # open|matched|completed
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    rows, total = list_pending(db, material_type, wanted_item, status, limit, offset)
    return RequestListOut(
        requests=[
            RequestRow(
                request_id=r.id,
                wanted_item=r.wanted_item,
                material_type=r.material_type,
                desired_amount=r.desired_amount,
                unit=r.unit,
                status=r.status,
            )
            for r in rows
        ],
        total=total,
    )
