# services/resource_service.py
from typing import Any, Dict, List, Tuple, Optional

from sqlalchemy.orm import Session
from models.user import User
from services.ai_client import (
    analyze_image,
    register_resource,
    list_resource,  
    _ensure_dict,
)

def auto_create_from_image(
    *,
    user: User,
    image_file,
    title: Optional[str] = None,
    description: Optional[str] = None,
    amount: Optional[float] = None,
    unit: Optional[str] = None,
    value: Optional[int] = None,
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:

    ai_resp_raw = analyze_image(image_file=image_file, username=user.username)
    ai_resp = _ensure_dict(ai_resp_raw)
    if ai_resp.get("resource_id"):
        return None, ai_resp

    analysis_id = ai_resp.get("analysis_id")
    if not analysis_id:
        raise ValueError("AI 응답에 analysis_id도 resource_id도 없습니다.")

    title = title or ai_resp.get("detected_item") or "Auto Resource"
    amount = amount if amount is not None else ai_resp.get("amount")
    unit = unit or ai_resp.get("unit")
    if value is None:
        value = ai_resp.get("estimated_value") or ai_resp.get("value")

    created = register_resource(
        analysis_id=analysis_id,
        title=title,
        description=description,
        amount=amount,
        unit=unit,
        value=value,
        username=user.username,
    )
    return ai_resp, created

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
            print(f"[WARN] list_resource failed for user={uname}: {e}")

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
