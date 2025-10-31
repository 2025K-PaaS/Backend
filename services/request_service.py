# services/request_service.py
from typing import Iterable, List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from models.user import User
from services.ai_client import get_all_requests


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.execute(select(User).where(User.username == username)).scalar_one_or_none()

def _filter_requests(rows: List[Dict[str, Any]],
                     material_type: Optional[str],
                     wanted_item: Optional[str],
                     username: Optional[str]) -> List[Dict[str, Any]]:
    def _ok(r: Dict[str, Any]) -> bool:
        if username and r.get("username") != username:
            return False
        if material_type and r.get("material_type") != material_type:
            return False
        if wanted_item:
            wi = (r.get("item_name") or "")
            if wanted_item.lower() not in wi.lower():
                return False
        return True
    return [r for r in rows if _ok(r)]

def _paginate(rows: List[Dict[str, Any]], limit: Optional[int], offset: Optional[int]) -> List[Dict[str, Any]]:
    if limit is None:
        return rows
    return rows[(offset or 0): (offset or 0) + limit]

def list_pending_from_ai(
    material_type: Optional[str],
    wanted_item: Optional[str],
    status: Optional[str],
    limit: Optional[int],
    offset: Optional[int],
) -> Tuple[List[Dict[str, Any]], int]:
    rows = get_all_requests(status=status)
    rows = _filter_requests(rows, material_type, wanted_item, username=None)
    total = len(rows)
    rows = _paginate(rows, limit, offset)
    return rows, total

def list_by_user_from_ai(
    username: str,
    material_type: Optional[str],
    wanted_item: Optional[str],
    status: Optional[str],
    limit: Optional[int],
    offset: Optional[int],
) -> Tuple[List[Dict[str, Any]], int]:
    rows = get_all_requests(status=status)
    rows = _filter_requests(rows, material_type, wanted_item, username=username)
    total = len(rows)
    rows = _paginate(rows, limit, offset)
    return rows, total

def get_by_id_from_ai(request_id: str, *, status: Optional[str] = None) -> Optional[dict]:
    if not request_id:
        return None

    rows, _total = list_pending_from_ai(
        material_type=None,
        wanted_item=None,
        status=status,
        limit=100_000,
        offset=0,
    )
    for r in rows or []:
        rid = str(r.get("request_id") or r.get("id") or "")
        if rid == str(request_id):
            return r
    return None

def get_map_by_ids_from_ai(request_ids: Iterable[str], *, status: Optional[str] = None) -> Dict[str, dict]:
    ids = {str(x) for x in (request_ids or []) if x}
    if not ids:
        return {}

    rows, _total = list_pending_from_ai(
        material_type=None,
        wanted_item=None,
        status=status,
        limit=100_000,
        offset=0,
    )
    out: Dict[str, dict] = {}
    for r in rows or []:
        rid = str(r.get("request_id") or r.get("id") or "")
        if rid in ids:
            out[rid] = r
    return out