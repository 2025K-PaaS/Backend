# services/point_service.py
from sqlalchemy.orm import Session
from sqlalchemy import select
from models.point import PointWallet, PointLedger

def _get_or_create_wallet(db: Session, user_id: int) -> PointWallet:
    wallet = db.get(PointWallet, user_id)
    if not wallet:
        wallet = PointWallet(user_id=user_id, balance=0)
        db.add(wallet)
        db.flush()  # no commit here
    return wallet

def get_balance(db: Session, user_id: int) -> int:
    wallet = _get_or_create_wallet(db, user_id)
    return int(wallet.balance or 0)

def get_history(db: Session, user_id: int, limit: int = 20, before_id: int | None = None):
    stmt = select(PointLedger).where(PointLedger.user_id == user_id)
    if before_id:
        stmt = stmt.where(PointLedger.id < before_id)
    stmt = stmt.order_by(PointLedger.id.desc()).limit(limit)
    rows = list(db.execute(stmt).scalars())
    next_before_id = rows[-1].id if rows and len(rows) == limit else None
    return rows, next_before_id

def award(
    db: Session,
    user_id: int,
    amount: int,
    reason: str,
    ref_type: str | None = None,
    ref_id: str | None = None,
    idempotency_key: str | None = None,
) -> int:
    """
    NOTE: 이 함수는 COMMIT하지 않습니다. 호출자가 commit 하세요.
    """
    if amount == 0:
        return get_balance(db, user_id)

    # idempotency 검사 (SQLAlchemy 2.x 스타일)
    if idempotency_key:
        exists_stmt = select(PointLedger.id).where(PointLedger.idempotency_key == idempotency_key).limit(1)
        if db.execute(exists_stmt).scalar() is not None:
            return get_balance(db, user_id)

    wallet = _get_or_create_wallet(db, user_id)
    wallet.balance = (wallet.balance or 0) + int(amount)

    entry = PointLedger(
        user_id=user_id,
        delta=int(amount),
        reason=reason,
        ref_type=ref_type,
        ref_id=str(ref_id) if ref_id is not None else None,
        idempotency_key=idempotency_key,
    )
    db.add(entry)
    db.flush()  # keep uncommitted
    return int(wallet.balance)
