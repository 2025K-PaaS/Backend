# services/resource_service.py
from typing import Any, Dict, List, Tuple, Optional
from core.config import settings
from sqlalchemy.orm import Session
from models.user import User
from models.analysis import Analysis
from services import point_service
from services.ai_client import (
    get_all_resources,
    register_resource,
    list_resource,
    _ensure_dict,
    get_match_by_resource,
    get_match_by_request
)
from services.request_service import get_by_id_from_ai

def finalize_resource(
    *,
    db: Session,
    user: User,
    analysis_id: str,
    title: Optional[str] = None,
    item_name: Optional[str] = None,
    description: Optional[str] = None,
    amount: Optional[float | int | str] = None, 
    value: Optional[int] = None,
    item_type: Optional[str] = None,  
    material_type: Optional[str] = None,
    matched_request_id: Optional[str] = None,
    image_path: Optional[str] = None,
) -> Dict[str, Any]:
    anal = (
        db.query(Analysis)
        .filter(Analysis.ai_analysis_id == analysis_id, Analysis.username == user.username)
        .first()
    )
    if not anal:
        raise ValueError("유효하지 않거나 소유자가 아닌 analysis_id 입니다.")


    title = title or getattr(anal, "suggested_title", None) or getattr(anal, "detected_item", None) or "Resource"
    item_name = (
        item_name
        or getattr(anal, "item_name", None)
        or title
    )
    material_type = material_type or getattr(anal, "material_type", None)
    item_type = item_type or getattr(anal, "detected_item", None)  
    if value is None:
        value = getattr(anal, "estimated_value", None)

    if not image_path:
        image_path = getattr(anal, "image_url", None) or getattr(anal, "image_path", None)

    amount_str = None if amount is None else str(amount)

    created = register_resource(
        analysis_id=analysis_id,
        title=title,
        description=description,
        amount=amount_str,        
        value=value or 0,
        username=user.username,      
        material_type=material_type,
        item_type=item_type, 
        item_name=item_name,
        matched_request_id=matched_request_id,
        image_path=image_path,
    )
    print("[🔥 AI 요청 응답]", created)  

    if hasattr(anal, "status"):
        try:
            anal.status = "used"
            db.add(anal); db.commit()
        except Exception:
            db.rollback()

    return created

def list_by_username(username: str) -> Tuple[List[Dict[str, Any]], int]:
    data = list_resource(username=username)
    raw_rows = data.get("resources", []) or []
    rows: List[Dict[str, Any]] = []
    for r in raw_rows:
        rec = _ensure_dict(r)
        rec["username"] = rec.get("username") or username 
        rows.append(rec)
    total = data.get("total", len(rows)) or len(rows)
    return rows, total

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
                    rec = _ensure_dict(r)
                    rec["username"] = rec.get("username") or uname 
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

    filtered = [_ensure_dict(r) for r in aggregated if pass_filter(_ensure_dict(r))]

    total = len(filtered)
    sliced = filtered[offset : offset + limit]

    for r in sliced:
        r.setdefault("status", "registered")

    return sliced, total


def _to_int(v, default=0):
    try:
        if v is None: return default
        return int(float(str(v)))
    except Exception:
        return default

def _parse_amount(v) -> Optional[float]:
    if v is None: return None
    s = str(v).replace(",", " ")
    buf, dot = "", False
    for ch in s:
        if ch.isdigit(): buf += ch
        elif ch == "." and not dot: buf += ch; dot = True
    try:
        return float(buf) if buf else None
    except Exception:
        return None

def award_points_if_matched(
    db: Session,
    resource_id: str,
    request_id: Optional[str] = None,
    allow_on_accept: bool = False,
):
    # 1) 매칭 상태 조회 (resource→request 순)
    match_data: Dict[str, Any] = {}
    try:
        match_data = get_match_by_resource(resource_id)
    except Exception:
        match_data = {}

    state = (match_data.get("status") or match_data.get("state") or "").lower()
    req_info = match_data.get("request") or {}
    res_info = match_data.get("resource") or {}

    if state not in ("matched", "completed", "accepted") and request_id:
        try:
            m2 = get_match_by_request(request_id)
            state2 = (m2.get("status") or m2.get("state") or "").lower()
            if state2 in ("matched", "completed", "accepted"):
                match_data = m2
                req_info = m2.get("request") or {}
                res_info = m2.get("resource") or {}
                state = state2
        except Exception:
            pass

    if state not in ("matched", "completed", "accepted"):
        if not allow_on_accept:
            print(f"[스킵] 상태 불일치 state={state}")
            return None
        # confirm 직후 강행 모드
        state = "accepted"

    # 2) 식별자/username
    matched_resource_id = (
        req_info.get("matched_resource_id")
        or res_info.get("resource_id")
        or resource_id
    )
    supplier_username = res_info.get("username")
    requester_username = req_info.get("username")

    # 3) value 해석 (여러 경로 보강)
    value, value_src = 0, None

    # 3-1) match.resource.value
    v0 = res_info.get("value")
    if v0 is not None:
        value = _to_int(v0, 0); value_src = "match.resource.value"

    # 3-2) list_resource(supplier)에서 해당 resource_id
    if (value <= 0) and supplier_username:
        try:
            data = list_resource(username=supplier_username, limit=1000, offset=0)
            for r in data.get("resources") or []:
                r = _ensure_dict(r)
                rid = r.get("resource_id") or r.get("id")
                if str(rid) == str(matched_resource_id):
                    v1 = r.get("value")
                    if v1 is not None:
                        value = _to_int(v1, 0); value_src = "list_resource.value"
                    # 비어있을 수도 있으니 username도 보강
                    supplier_username = r.get("username") or supplier_username
                    break
        except Exception as e:
            print(f"[경고] list_resource 실패: {e}")

    # 3-3) get_all_resources()
    if value <= 0:
        try:
            for r in get_all_resources():
                rid = r.get("resource_id") or r.get("id")
                if str(rid) == str(matched_resource_id):
                    v2 = r.get("value")
                    if v2 is not None:
                        value = _to_int(v2, 0); value_src = "all_resources.value"
                    supplier_username = r.get("username") or supplier_username
                    break
        except Exception as e:
            print(f"[경고] get_all_resources 실패: {e}")

    # 3-4) 기본 포인트
    if value <= 0:
        value = int(settings.MATCH_DEFAULT_POINT or 0)
        value_src = "default_point"

    if value <= 0:
        print(f"[스킵] value 해석 실패 (resource_id={matched_resource_id})")
        return None

    # 4) 요청자 username 보강
    if not requester_username and request_id:
        req_obj = get_by_id_from_ai(request_id, status=None)
        if req_obj:
            requester_username = req_obj.get("username")
            # 타이틀/수량 보강
            req_info.setdefault("item_name", req_obj.get("item_name"))
            req_info.setdefault("amount", req_obj.get("amount"))

    # 5) 유저 resolve
    supplier = db.query(User).filter_by(username=supplier_username).first() if supplier_username else None
    requester = db.query(User).filter_by(username=requester_username).first() if requester_username else None
    if not supplier or not requester:
        print(f"[스킵] 지급 대상 부재 supplier={supplier_username}, requester={requester_username}")
        return None

    item_title = (req_info.get("item_name")) or "자원 매칭"
    item_amount = _parse_amount(req_info.get("amount"))

    # 6) 양쪽(중복 제거) 지급
    try:
        seen = set()
        for u in [supplier, requester]:
            if u.id in seen:  # self-match 방지
                continue
            seen.add(u.id)
            point_service.award(
                db=db,
                user_id=u.id,
                amount=value,
                ref_type="resource",
                ref_id=matched_resource_id,
                item_title=item_title,
                item_amount=item_amount,
                idempotency_key=f"match:{matched_resource_id}:{u.id}",
            )
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[에러] 포인트 지급 중 예외: {e}")
        raise

    print(f"[포인트 지급 완료] rid={matched_resource_id}, value={value}({value_src}), state={state}, supplier={supplier_username}, requester={requester_username}")
    return {
        "status": "ok",
        "value": value,
        "value_source": value_src,
        "state": state,
        "resource_id": matched_resource_id,
        "supplier": supplier_username,
        "requester": requester_username,
    }
