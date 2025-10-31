# routers/points.py

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from core.deps import get_db, get_current_user
from core.config import settings
from services import point_service
from services.resource_service import award_points_if_matched
from schemas.point import PointBalanceOut, PointHistoryOut, PointHistoryItem, GrantPointsIn, PointHistoryAllOut

router = APIRouter(prefix="/points", tags=["points"])


def require_admin_key(x_admin_key: str | None = Header(default=None)):
    if not x_admin_key or x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="invalid admin key")
    return True



@router.get("/me", response_model=PointBalanceOut)
def my_balance(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return point_service.get_balance_status(db, current_user.id)


@router.get("/me/history", response_model=PointHistoryOut)
def my_history(
    limit: int = Query(20, ge=1, le=100),
    before_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """현재 로그인한 유저의 포인트 내역 조회 (자원명, 수량 포함)"""
    rows, next_before_id = point_service.get_history(db, current_user.id, limit, before_id)

    items = [
        PointHistoryItem(
            id=r.id,
            delta=r.delta,
            ref_type=r.ref_type,
            ref_id=r.ref_id,
            item_title=r.item_title or "관리자 지급",
            item_amount=r.item_amount,
            created_at=r.created_at,
        )
        for r in rows
    ]

    return PointHistoryOut(items=items, next_before_id=next_before_id)


@router.get(
    "/me/all",
    response_model=PointHistoryAllOut,
    response_model_exclude_none=True
)
def my_history_all(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    rows = point_service.get_all(db, current_user.id)
    summary = point_service.get_balance_status(db, current_user.id)

    items = [
        PointHistoryItem(
            id=r.id,
            delta=r.delta,
            ref_type=r.ref_type,
            ref_id=r.ref_id,
            item_title=r.item_title or "관리자 지급",
            item_amount=r.item_amount,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return {**summary, "items": items}


@router.post(
    "/grant",
    response_model=PointBalanceOut,
    dependencies=[Depends(require_admin_key)],
)
def grant_points(
    payload: GrantPointsIn,
    db: Session = Depends(get_db),
):
    point_service.award(
        db,
        user_id=payload.user_id,
        amount=payload.amount,
        idempotency_key=payload.idempotency_key,
    )
    db.commit()
    return point_service.get_balance_status(db, payload.user_id)

@router.post("/award")
def award_matched_points(
    resource_id: str = Query(..., description="AI 서버의 resource_id"),
    db: Session = Depends(get_db),
):
    result = award_points_if_matched(db, resource_id)
    if not result:
        raise HTTPException(status_code=400, detail="지급 조건을 만족하지 않거나 AI 서버 조회 실패")
    return result