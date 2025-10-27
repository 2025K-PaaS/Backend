# routers/points.py

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from core.deps import get_db, get_current_user
from core.config import settings
from services import point_service
from schemas.point import PointBalanceOut, PointHistoryOut, GrantPointsIn

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
    items, next_before_id = point_service.get_history(
        db, current_user.id, limit, before_id
    )
    return PointHistoryOut(items=items, next_before_id=next_before_id)


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
        reason=payload.reason,
        idempotency_key=payload.idempotency_key,
    )
    db.commit()
    return point_service.get_balance_status(db, payload.user_id)
