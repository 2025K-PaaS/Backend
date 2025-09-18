# services/point_service.py

from sqlalchemy.orm import Session
from sqlalchemy import select, update
from models.point import PointWallet, PointLedger

def _get_or_create_wallet(db: Session, user_id: int) -> PointWallet:
    wallet = db.get(PointWallet, user_id)
    if not wallet:
        wallet = PointWallet(user_id=user_id, balance=0)
        db.add(wallet)
        db.flush()  
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
    if amount == 0:
        return get_balance(db, user_id)

    # 이미 같은 키로 적립된 적이 있으면 스킵
    if idempotency_key:
        exists = db.query(PointLedger).filter_by(idempotency_key=idempotency_key).first()
        if exists:
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
    db.flush()
    return int(wallet.balance)
