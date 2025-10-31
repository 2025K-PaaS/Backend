# routers/resources.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core.utils import make_public_url
from core.deps import get_db, get_current_user
from services.resource_service import finalize_resource, list_by_username, list_all_resources
from schemas.resource import (
    ResourceCreateIn,  
    ResourceCreateOut,
    MatchedRequest,
    ResourceListOut,
    ResourceRow,
)
from services.request_service import get_map_by_ids_from_ai 
from services.ai_client import get_match_by_resource 

router = APIRouter(prefix="/resources", tags=["resources"])

def _extract_requests_from_match_resp(match_resp: dict | list) -> list[dict]:
    out: list[dict] = []

    def _dig(x):
        if isinstance(x, list):
            for e in x:
                _dig(e)
        elif isinstance(x, dict):
            for key in ["matches", "matched_requests", "requests", "items", "candidates"]:
                v = x.get(key)
                if isinstance(v, list):
                    out.extend([e for e in v if isinstance(e, dict)])
            if isinstance(x.get("request"), dict):
                out.append(x["request"])
            if isinstance(x.get("data"), (dict, list)):
                _dig(x["data"])

    _dig(match_resp)
    return out

def _normalize_basic(row: dict) -> dict:
    rid = row.get("request_id") or row.get("id")
    title = row.get("title") or row.get("item_name") or row.get("wanted_item")
    wanted_item = row.get("item_name") or row.get("wanted_item") or title
    amt = row.get("amount") or row.get("desired_amount")
    return {
        "request_id": rid,
        "item_name": wanted_item,
        "item_type": row.get("item_type"),
        "material_type": row.get("material_type"),
        "amount": amt,
        "title": row.get("title"),
        "description": row.get("description"),
        "image_url": row.get("image_url") or row.get("image_path"),
        "username": row.get("username"),
    }

def _to_matched_request(row: dict) -> MatchedRequest:
    n = _normalize_basic(row)
    img_url = make_public_url(n["image_url"]) if n.get("image_url") else None
    return MatchedRequest(
        request_id    = n["request_id"],
        wanted_item   = n["item_name"] or n["wanted_item"],
        material_type = n["material_type"],
        desired_amount= n.get("desired_amount") or n["amount"],
        title         = n.get("title"),
        description   = n.get("description"),
        image_url     = img_url,
        item_type = n.get("item_type"),
        username      = n.get("username"),
    )


@router.post("", response_model=ResourceCreateOut, status_code=201)
def create_resource(
    payload: ResourceCreateIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        resp = finalize_resource(
            db=db,
            user=current_user,
            analysis_id=payload.analysis_id,
            title=payload.title,
            item_name=payload.item_name,   
            description=payload.description,
            amount=payload.amount or 1,
            value=payload.value or 0,
            item_type=payload.item_type,   
            material_type=payload.material_type,
            matched_request_id=payload.matched_request_id,
            image_path=payload.image_path,
        )
        print("[AI 응답]", resp)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not isinstance(resp, dict):
        raise HTTPException(status_code=502, detail="AI 서버 응답 형식 오류")

    data = resp.get("data") or resp
    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="AI 서버 응답 파싱 실패")

    resource_id = data.get("resource_id") or data.get("id")
    status      = data.get("status") or "registered"
    message     = data.get("message") or "자원이 성공적으로 등록되었습니다."

    if not resource_id:
        raise HTTPException(status_code=502, detail="AI 응답에 resource_id 가 없습니다.")

    matched_requests: list[MatchedRequest] = []
    try:
        match_resp = get_match_by_resource(resource_id)
        candidates = _extract_requests_from_match_resp(match_resp)

        if not candidates and isinstance(match_resp, dict) and isinstance(match_resp.get("request"), dict):
            candidates = [match_resp["request"]]

        prelim = []
        ids = []
        for c in candidates or []:
            b = _normalize_basic(c)
            rid = b.get("request_id")
            if rid:
                prelim.append(b)
                ids.append(str(rid))

        idmap = get_map_by_ids_from_ai(ids, status=None) if ids else {}

        enriched = []
        for b in prelim:
            rid = str(b["request_id"])
            d = idmap.get(rid)
            if isinstance(d, dict):
                dn = _normalize_basic(d)
                for k, v in dn.items():
                    if v and (not b.get(k)):
                        b[k] = v
            enriched.append(b)

        matched_requests = [_to_matched_request(x) for x in enriched]

    except Exception as e:
        print(f"[경고] /match/by_resource 병합 실패: {e}")
        matched_requests = []

    return ResourceCreateOut(
        resource_id=resource_id,
        status=status,
        message=message,
        matched_requests=matched_requests,
    )

@router.get("/myresource", response_model=ResourceListOut)
def list_my_resources(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        rows, total = list_by_username(current_user.username)
    except Exception as e:
        print("예외 발생. 로그는:", e)
        raise HTTPException(status_code=400, detail=str(e))

    return ResourceListOut(
        resources=[
            ResourceRow(
                resource_id=r.get("resource_id") or r.get("id"),
                username=r.get("username"),  
                title=r.get("title"),
                item_name=r.get("item_name"),
                item_type=r.get("item_type") or r.get("detected_item"),
                material_type=r.get("material_type"),
                amount=r.get("amount") or 0,
                value=int(r.get("value") or 0),
                status=r.get("status", "registered"),
                image_url=make_public_url(r.get("image_url") or r.get("image_path")),
                description=r.get("description"),
            )
            for r in rows
        ],
        total=total,
    )

@router.get("/all", response_model=ResourceListOut)
def list_all(
    material_type: str | None = Query(None, description="자원 종류 필터 (예: 플라스틱, 데님 등)"),
    status: str | None = Query(None, description="상태 필터 (registered, matched, in_progress 등)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    try:
        rows, total = list_all_resources(
            db=db,
            material_type=material_type,
            status=status,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ResourceListOut(
        resources=[
            ResourceRow(
                resource_id=r.get("resource_id") or r.get("id"),
                username=r.get("username"),  
                title=r.get("title"),
                item_name=r.get("item_name"), 
                item_type=r.get("item_type") or r.get("detected_item"),
                material_type=r.get("material_type"),
                amount=float(r.get("amount") or 0),
                value=int(r.get("value") or 0),
                status=r.get("status"),
                image_url=make_public_url(r.get("image_url") or r.get("image_path")),
                description=r.get("description"),
            )
            for r in rows
        ],
        total=total,
    )

