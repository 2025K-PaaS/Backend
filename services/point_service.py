# services/point_service.py
from typing import Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func    
from models.point import PointWallet, PointLedger

_LEVEL_TABLE = [
    (0,    "새싹 탐험가"),      # Lv1
    (100,  "씨앗 수호자"),      # Lv2
    (300,  "지구 지킴이"),      # Lv3
    (600,  "순환 장인"),        # Lv4
    (1000, "지구 영웅"),        # Lv5
]

def _calc_level_info(balance: int) -> Tuple[int, str]:
    chosen_level_idx = 0
    for idx, (min_pt, _title) in enumerate(_LEVEL_TABLE):
        if balance >= min_pt:
            chosen_level_idx = idx
        else:
            break

    _, title = _LEVEL_TABLE[chosen_level_idx]
    level_number = chosen_level_idx + 1
    return level_number, title


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


def get_lifetime_earned(db: Session, user_id: int) -> int:
    stmt = (
        select(func.coalesce(func.sum(PointLedger.delta), 0))
        .where(
            PointLedger.user_id == user_id,
            PointLedger.delta > 0
        )
    )
    total = db.execute(stmt).scalar()
    return int(total or 0)


def get_balance_status(db: Session, user_id: int) -> Dict[str, Any]:
    balance = get_balance(db, user_id)
    lifetime = get_lifetime_earned(db, user_id)
    level_num, level_title = _calc_level_info(balance)

    return {
        "balance": balance,
        "lifetime_earned": lifetime,
        "level": level_num,
        "title": level_title,
    }


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

    if idempotency_key:
        exists_stmt = (
            select(PointLedger.id)
            .where(PointLedger.idempotency_key == idempotency_key)
            .limit(1)
        )
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
    db.flush()
    return int(wallet.balance)
