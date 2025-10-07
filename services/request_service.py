# services/request_service.py

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from models.request import Request

def create(db: Session, created_by: int | None, **payload) -> Request:
    req = Request(created_by=created_by, **payload)
    db.add(req)
    db.commit()
    db.refresh(req)
    return req

def list_pending(db: Session, material_type, wanted_item, status, limit, offset):
    stmt = select(Request).order_by(Request.created_at.desc())
    if material_type:
        stmt = stmt.where(Request.material_type == material_type)
    if wanted_item:
        stmt = stmt.where(Request.wanted_item.ilike(f"%{wanted_item}%"))
    if status:
        stmt = stmt.where(Request.status == status)

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.execute(stmt.limit(limit).offset(offset)).scalars().all()
    return rows, (total or 0)
