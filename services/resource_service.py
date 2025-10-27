# services/resource_service.py
from typing import Any, Dict, List, Tuple, Optional

from sqlalchemy.orm import Session
from models.user import User
from models.analysis import Analysis
from services.ai_client import (
    analyze_image,
    register_resource,
    list_resource,  
    _ensure_dict,
)

def finalize_resource(
    *,
    db: Session,
    user: User,
    analysis_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    amount: Optional[float] = None,
    unit: Optional[str] = None,
    value: Optional[int] = None,
    material_type: Optional[str] = None,
    condition: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    # 1) 소유권 검증: 로컬 Analysis 테이블에서 확인
    anal = (
        db.query(Analysis)
        .filter(
            Analysis.ai_analysis_id == analysis_id,
            Analysis.username == user.username,
        )
        .first()
    )
    if not anal:
        raise ValueError("유효하지 않거나 소유자가 아닌 analysis_id 입니다.")

    # 2) AI 서버에 최종 등록 위임
    created = register_resource(
        analysis_id=analysis_id,
        title=title,
        description=description,
        amount=amount,
        unit=unit,
        value=value,
        username=user.username,
        material_type=material_type,
        condition=condition,
        tags=tags,
    )

    # 3) (선택) 상태 마킹: Analysis에 status 필드가 있다면 used 로 갱신
    if hasattr(anal, "status"):
        try:
            anal.status = "used"
            db.add(anal)
            db.commit()
        except Exception:
            db.rollback()

    return created

# 로그인 사용자의 자원 목록 조회
def list_by_username(username: str) -> Tuple[List[Dict[str, Any]], int]:
    data = list_resource(username=username)
    raw_rows = data.get("resources", []) or []
    flat_rows: List[Dict[str, Any]] = []
    for r in raw_rows:
        if isinstance(r, list):
            flat_rows.extend(r)
        else:
            flat_rows.append(r)
    rows = [_ensure_dict(r) for r in flat_rows]
    total = data.get("total", 0) or 0
    return rows, total

# DB의 모든 사용자 username을 이용해 전체 자원 목록 조회
def list_all_resources(
    db: Session,
    material_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[List[Dict[str, Any]], int]:
    usernames: List[str] = [u.username for u in db.query(User).with_entities(User.username).all()]

    aggregated: List[Dict[str, Any]] = []
    for uname in usernames:
        try:
            data = list_resource(
                username=uname,
                material_type=material_type,
                status=status,
                limit=1000,   
                offset=0,
            )
            user_rows = data.get("resources", []) or []
            for r in user_rows:
                if isinstance(r, list):
                    aggregated.extend(r)
                else:
                    aggregated.append(r)
        except Exception as e:
            print(f"[경고] 사용자 {uname}의 자원 목록 조회에 실패했습니다: {e}")

    def pass_filter(rec: Dict[str, Any]) -> bool:
        if material_type and rec.get("material_type") != material_type:
            return False
        if status and rec.get("status") != status:
            return False
        return True

    filtered = [ _ensure_dict(r) for r in aggregated if pass_filter(_ensure_dict(r)) ]

    total = len(filtered)
    sliced = filtered[offset : offset + limit]

    for r in sliced:
        r.setdefault("status", "registered")

    return sliced, total
