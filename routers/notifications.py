# routers/notifications.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Literal
from pydantic import BaseModel, Field
import time 
from core.deps import get_db, get_current_user
from core.utils import make_public_url

from services.ai_client import (
    list_resource,
    get_match_by_resource,
    get_match_by_request,
    confirm_match,
    manual_match as ai_manual_match,
    get_match_history,  
)
from services.request_service import list_by_user_from_ai
from services.resource_service import award_points_if_matched
from schemas.notification import (
    ResourceBrief, RequestBrief,
    MatchProposalItem,
    MatchProposalsOut, ManualMatchIn, ManualMatchResponse
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _pub(url_or_path: str | None) -> str | None:
    if not url_or_path:
        return None
    return make_public_url(url_or_path)


@router.get("", response_model=MatchProposalsOut)
def list_my_match_proposals(
    state: str | None = Query(
        None,
        description='필터 상태("proposed"|"matched"|"declined"|"accepted"|None)',
    ),
    db: Session = Depends(get_db), 
    current_user=Depends(get_current_user),
):
    proposals: List[MatchProposalItem] = []

    # 입력 state 정규화(accepted → matched)
    if state is not None:
        state = state.lower()
        state = "matched" if state == "accepted" else state

    def _norm_state(x: str | None) -> str:
        raw = (x or "").lower()
        return "matched" if raw == "accepted" else (raw or "unknown")

    def _s(x) -> str | None:
        return str(x) if x is not None else None

    seen: set[tuple[str, str, str]] = set()  

    # 제안된 매칭
    try:
        rdata = list_resource(username=current_user.username)
        resources: List[Dict[str, Any]] = rdata.get("resources") or []

        res_map: Dict[str, Dict[str, Any]] = {}
        for r in resources:
            rid = (r.get("resource_id") or r.get("id"))
            if rid:
                res_map[str(rid)] = r

        for rid, r in res_map.items():
            try:
                m = get_match_by_resource(rid)
            except Exception:
                continue

            raw_state = str((m or {}).get("status") or (m or {}).get("state") or "")
            st = _norm_state(raw_state)

            default_states = {"proposed", "matched", "declined"} if state is None else {state}
            if st not in default_states:
                continue

            req = (m or {}).get("request") or {}
            req_id = req.get("request_id") or req.get("id") or ""
            key = (str(rid), str(req_id), st)
            if key in seen:
                continue
            seen.add(key)

            proposals.append(
                MatchProposalItem(
                    state=st,
                    role="supplier",
                    resource=ResourceBrief(
                        resource_id=str(rid),
                        title=r.get("title"),
                        item_name=r.get("title") or r.get("item_name"),
                        description=r.get("description"),
                        amount=_s(r.get("amount")),
                        value=int(r.get("value") or 0),
                        username=r.get("username"),
                        item_type=r.get("item_type"),
                        material_type=r.get("material_type"),
                        image_url=_pub(r.get("image_url") or r.get("image_path")),
                        status=r.get("status"),
                    ),
                    request=RequestBrief(
                        request_id=req.get("request_id") or req.get("id") or "",
                        item_name=req.get("item_name") or req.get("title"),
                        title=req.get("title"), 
                        amount=_s(req.get("amount")),
                        value=(int(req.get("value")) if req.get("value") is not None else None),
                        description=req.get("description"),
                        username=req.get("username"),
                        item_type=req.get("item_type"),
                        material_type=req.get("material_type"),
                        image_url=_pub(req.get("image_path") or req.get("image_url")),
                        status=req.get("status"),
                    ),
                )
            )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"자원 제안 조회 실패: {e}")

    try:
        my_rows, _total = list_by_user_from_ai(
            username=current_user.username,
            material_type=None,
            wanted_item=None,
            status=None,
            limit=None,
            offset=None,
        )

        for row in my_rows:
            request_id = (
                str(row.get("request_id"))
                if row.get("request_id") is not None
                else str(row.get("id") or "")
            )
            if not request_id:
                continue

            try:
                m = get_match_by_request(request_id)
            except Exception:
                continue

            raw_state = str((m or {}).get("status") or (m or {}).get("state") or "")
            st = _norm_state(raw_state)
            if state is not None and st != state:
                continue

            res = (m or {}).get("resource") or {}
            rid = res.get("resource_id") or res.get("id") or ""
            key = (str(rid), str(request_id), st)
            if key in seen:
                continue
            seen.add(key)

            proposals.append(
                MatchProposalItem(
                    state=st,
                    role="requester",
                    resource=ResourceBrief(
                        resource_id=str(rid),
                        title=res.get("title"),
                        item_name=res.get("title") or res.get("item_name"),
                        amount=_s(res.get("amount")),
                        value=int(res.get("value") or 0) if res.get("value") is not None else None,
                        username=res.get("username"),
                        description=res.get("description"),
                        item_type=res.get("item_type"),
                        material_type=res.get("material_type"),
                        image_url=_pub(res.get("image_path") or res.get("image_url")),
                        status=res.get("status"),
                    ),
                    request=RequestBrief(
                        request_id=request_id,
                        item_name=row.get("item_name") or row.get("wanted_item"),
                        title=row.get("title"),  
                        amount=_s(row.get("amount") if row.get("amount") is not None else row.get("desired_amount")),
                        value=(int(row.get("value")) if row.get("value") is not None else None),
                        description=row.get("description"),
                        username=row.get("username") or current_user.username,
                        item_type=row.get("item_type"),
                        material_type=row.get("material_type"),
                        image_url=_pub(row.get("image_path") or row.get("image_url")),
                        status=row.get("status"),
                    ),
                )
            )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"요청 제안 조회 실패: {e}")

    # 과거 히스토리(accepted/declined) 
    try:
        history = get_match_history(username=current_user.username)
        for h in history or []:
            raw_state = str(h.get("status") or "").lower()          # accepted | declined
            st = _norm_state(raw_state)                             # accepted → matched
            if state is not None and st != state:
                continue

            hr = h.get("resource") or {}
            hq = h.get("request") or {}
            rid = hr.get("resource_id") or hr.get("id") or ""
            qid = hq.get("request_id") or hq.get("id") or ""

            # 현재 유저가 supplier / requester 어떤 역할인지 판별
            role = None
            if (hr.get("username") or "").strip() == current_user.username:
                role = "supplier"
            elif (hq.get("username") or "").strip() == current_user.username:
                role = "requester"
            else:
                continue 

            key = (str(rid), str(qid), st)
            if key in seen:
                continue
            seen.add(key)

            proposals.append(
                MatchProposalItem(
                    state=st,
                    role=role, 
                    resource=ResourceBrief(
                        resource_id=str(rid),
                        title=hr.get("title"),
                        item_name=hr.get("title") or hr.get("item_name"),
                        description=hr.get("description"),
                        amount=_s(hr.get("amount")),
                        value=(int(hr.get("value")) if hr.get("value") is not None else None),
                        username=hr.get("username"),
                        item_type=hr.get("item_type"),
                        material_type=hr.get("material_type"),
                        image_url=_pub(hr.get("image_path") or hr.get("image_url")),
                        status=hr.get("status"),
                    ),
                    request=RequestBrief(
                        request_id=str(qid),
                        title=hr.get("title"),
                        item_name=hq.get("item_name") or hq.get("title"),
                        amount=_s(hq.get("amount")),
                        value=(int(hr.get("value")) if hr.get("value") is not None else None),
                        description=hq.get("description"),
                        username=hq.get("username"),
                        item_type=hq.get("item_type"),
                        material_type=hq.get("material_type"),
                        image_url=_pub(hq.get("image_path") or hq.get("image_url")),
                        status=hq.get("status"),
                        is_auto_written=hq.get("is_auto_written", False),
                    ),
                )
            )
    except Exception as e:
        print(f"[경고] /match/history 조회 실패: {e}")

    return MatchProposalsOut(proposals=proposals, total=len(proposals))


def _extract_state(m: dict | None) -> str:
    if not m:
        return ""
    return str(m.get("status") or m.get("state") or "").lower()

def _is_matched_state(m: dict | None) -> bool:
    if not m:
        return False
    st = str(m.get("status") or "").lower()
    return st in {"matched", "completed", "accepted"}

def _try_award_on_matched(
    db: Session,
    resource_id: str,
    request_id: str,
    tries: int = 6,
    delay_sec: float = 0.5,
) -> dict:
    last_state = ""
    last_match = None

    for _ in range(tries):
        match = None
        try:
            match = get_match_by_resource(resource_id)
        except Exception:
            match = None

        if not _is_matched_state(match):
            try:
                match = get_match_by_request(request_id)
            except Exception:
                match = None

        last_match = match
        last_state = _extract_state(match)

        if _is_matched_state(match):
            rid = (
                ((match.get("request") or {}).get("matched_resource_id"))
                or ((match.get("resource") or {}).get("resource_id"))
                or resource_id
            )
            res = award_points_if_matched(db, rid)
            if not res:
                return {"awarded": False, "reason": "award skipped or failed", "state": last_state}
            return {"awarded": True, "detail": res, "state": last_state}

        time.sleep(delay_sec)

    return {"awarded": False, "reason": "not matched after retries", "state": last_state, "raw": last_match}



class ConfirmIn(BaseModel):
    resource_id: str
    request_id: str
    action: Literal["accept", "decline", "reject"] = Field(
        ...,
        description="수락/거절",
    )


@router.post("/confirm")
def confirm_my_match(
    body: ConfirmIn,
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    action = "decline" if body.action == "reject" else body.action

    try:
        confirm_res = confirm_match(body.resource_id, body.request_id, action)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"매칭 확정 실패: {e}")

    award_info = None
    if action == "accept":
        try:
            award_info = award_points_if_matched(
                db,
                resource_id=body.resource_id,
                request_id=body.request_id,
                allow_on_accept=True,
            )
            if not award_info:
                award_info = {"awarded": False, "reason": "award skipped or failed"}
            else:
                award_info = {"awarded": True, "detail": award_info}
        except Exception as e:
            award_info = {"awarded": False, "error": str(e)}

    return {"confirm": confirm_res, "award": award_info}


@router.post("/iwant", response_model=ManualMatchResponse, status_code=201)
def manual_match(
    body: ManualMatchIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        ai_res = ai_manual_match(
            resource_id=body.resource_id,
            amount=body.amount,
            username=current_user.username,   
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI 수동매칭 실패: {e}")

    return ManualMatchResponse(manual=ai_res, award=None)