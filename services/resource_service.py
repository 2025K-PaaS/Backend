# services/resource_service.py
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from models.analysis import Analysis
from models.resource import Resource
from models.request import Request
from models.user import User
from models.resource import ResourceStatus  # enum 사용

def create_from_ai_analysis(
    db: Session,
    user_id: int,
    ai_analysis_id: str,
    title: str,
    description: str | None,
    amount: float,
    unit: str,
    value: int,
):
    anal = db.execute(
        select(Analysis).where(Analysis.ai_analysis_id == ai_analysis_id)
    ).scalar_one_or_none()
    if not anal:
        raise ValueError("invalid analysis_id")

    res = Resource(
        user_id=user_id,
        analysis_id=anal.id,
        title=title,
        description=description,
        amount=amount,
        unit=unit,
        value=value,
        detected_item=anal.detected_item,
        material_type=anal.material_type,
        status=ResourceStatus.registered,  
    )
    db.add(res)
    db.commit()
    db.refresh(res)

    # 간단 매칭 규칙: 같은 품목/재질 + 동일 단위 + 요청 상태 open
    q = select(Request).where(Request.unit == unit).where(Request.status == "open")
    if anal.detected_item:
        q = q.where(Request.wanted_item == anal.detected_item)
    if anal.material_type:
        q = q.where(Request.material_type == anal.material_type)

    matches = db.execute(q).scalars().all()
    return res, matches

def list_by_username(db: Session, username: str):
    stmt = (
        select(Resource)
        .join(User, Resource.user_id == User.id)
        .where(User.username == username)
        .order_by(Resource.created_at.desc())
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.execute(stmt).scalars().all()
    return rows, (total or 0)
