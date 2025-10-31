# routers/requests.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from pathlib import Path
import os, uuid
import requests
from core.deps import get_db, get_current_user
from core.utils import make_public_url, make_ai_url

from services.request_service import (
    list_pending_from_ai,
    list_by_user_from_ai,
    get_user_by_username,
    get_by_id_from_ai, 
)
from services.ai_client import create_request_on_ai

from schemas.request import (
    RequestOut, RequestListOut, 
    RequestRow, RequestListWithAddressOut,
    RequestDetailOut,
)

router = APIRouter(prefix="/requests", tags=["requests"])

UPLOAD_DIR = Path("uploads/requests")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def _save_upload_file(up: UploadFile) -> str:
    ext = os.path.splitext(up.filename or "")[1].lower()
    name = f"{uuid.uuid4().hex}{ext}"
    path = UPLOAD_DIR / name
    up.file.seek(0)
    with open(path, "wb") as f:
        f.write(up.file.read())
    return str(path).replace("\\", "/")


def _to_float(v) -> float:
    try:
        s = str(v).strip()
        num = ""
        for ch in s:
            if (ch.isdigit() or ch in ".-+eE"):
                num += ch
            else:
                if num:
                    break
        return float(num) if num else float(s)
    except:
        return 0.0

@router.post("", response_model=RequestOut, status_code=201)
def create_request(
    title: str | None = Form(None), 
    item_name: str | None = Form(None),
    amount: str | None = Form(None),
    description: str | None = Form(None),
    item_type: str | None = Form(None),
    material_type: str | None = Form(None),
    image: UploadFile | None = File(None),
    _db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not item_name:
        raise HTTPException(status_code=422, detail="물품명을 입력해주세요.")
    if not amount:
        raise HTTPException(status_code=422, detail="수량을 입력해주세요.")
    if not description:
        raise HTTPException(status_code=422, detail="설명을 입력해주세요.")
    if not title:
        title = item_name 

    image_path = None
    if image:
        try:
            image_path = _save_upload_file(image)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"이미지 저장 실패: {e}")
    image_url = make_public_url(image_path) if image_path else None
    ai_payload = {
        "title": title,      
        "item_name": item_name,
        "amount": amount,
        "description": description or "",
        "username": current_user.username,
        "item_type": item_type or "",
        "material_type": material_type or "",
        "image_path": image_url,  
    }

    try:
        ai_resp = create_request_on_ai(ai_payload) 

        if isinstance(ai_resp, dict) and isinstance(ai_resp.get("data"), dict):
            base = ai_resp["data"]
        elif isinstance(ai_resp, dict):
            base = ai_resp
        else:
            base = {}

        request_id = (
            base.get("request_id")
            or base.get("id")
            or base.get("requestId")
        )
        status = base.get("status", "pending")
        message = base.get("message", "요청이 성공적으로 등록되었습니다.")

        if not request_id:
            raise ValueError(f"AI 응답 파싱 실패: request_id 없음. raw={ai_resp}")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"AI 호출 실패: {e}")

    
    return RequestOut(
        request_id=str(request_id),
        image_url=image_url,
        status=status,
        message=message,
    )


@router.get("/all", response_model=RequestListOut)
def get_pending_requests(
    material_type: str | None = Query(default=None),
    wanted_item: str | None = Query(default=None),
    status: str | None = Query(default=None),  
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    rows, total = list_pending_from_ai(
        material_type=material_type,
        wanted_item=wanted_item,
        status=status,
        limit=limit,
        offset=offset,
    )
    return RequestListOut(
        requests=[
            RequestRow(
                request_id=str(r.get("request_id") or r.get("id")),
                title=r.get("title") or r.get("item_name") or "",
                wanted_item=r.get("item_name") or "",
                item_type=r.get("item_type"), 
                material_type=r.get("material_type"),
                desired_amount=_to_float(r.get("amount")),
                description=r.get("description"),
                image_url=make_public_url(r.get("image_path")) if r.get("image_path") else None,
                status=r.get("status") or "pending",
                is_auto_written=r.get("is_auto_written", False), 
            )
            for r in rows
        ],
        total=total,
    )

@router.get("/me", response_model=RequestListOut)
def get_my_requests(
    material_type: str | None = Query(default=None),
    wanted_item: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int | None = Query(default=None),
    offset: int | None = Query(default=None),
    current_user=Depends(get_current_user),
):
    rows, total = list_by_user_from_ai(
        username=current_user.username,
        material_type=material_type,
        wanted_item=wanted_item,
        status=status,
        limit=limit,
        offset=offset,
    )
    return RequestListOut(
        requests=[
            RequestRow(
                request_id=str(r.get("request_id") or r.get("id")),
                title=r.get("title") or r.get("item_name") or "",
                wanted_item=r.get("item_name") or "",
                item_type=r.get("item_type"),     
                material_type=r.get("material_type"),
                desired_amount=_to_float(r.get("amount")),
                description=r.get("description"),
                image_url=make_public_url(r.get("image_path")) if r.get("image_path") else None,
                status=r.get("status") or "pending",
                is_auto_written=r.get("is_auto_written", False), 
            )
            for r in rows
        ],
        total=total,
    )

@router.get("/{username}", response_model=RequestListWithAddressOut)
def get_requests_by_username(
    username: str,
    material_type: str | None = Query(default=None),
    wanted_item: str | None = Query(default=None),
    status: str | None = Query(default=None),  
    limit: int | None = Query(default=None),
    offset: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    rows, total = list_by_user_from_ai(
        username=username,
        material_type=material_type,
        wanted_item=wanted_item,
        status=status,
        limit=limit,
        offset=offset,
    )

    return RequestListWithAddressOut(
        username=user.username,
        address=user.address,
        phone=user.phone,
        requests=[
            RequestRow(
                request_id=str(r.get("request_id") or r.get("id")),
                title=r.get("title") or r.get("item_name") or "",
                wanted_item=r.get("item_name") or "",
                item_type=r.get("item_type"),
                material_type=r.get("material_type"),
                desired_amount=_to_float(r.get("amount")),
                description=r.get("description"),
                image_url=make_public_url(r.get("image_path")) if r.get("image_path") else None,
                status=r.get("status") or "pending",
                is_auto_written=r.get("is_auto_written", False), 
            )
            for r in rows
        ],
        total=total,
    )


@router.get("/{request_id}", response_model=RequestDetailOut)
def get_request_by_id(
    request_id: str,
    _db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    raw = get_by_id_from_ai(request_id=request_id, status=None)
    if not raw:
        raise HTTPException(status_code=404, detail="Request not found")

    rid = str(raw.get("request_id") or raw.get("id") or request_id)
    title = raw.get("title") or raw.get("item_name") or raw.get("wanted_item") or ""
    wanted_item = raw.get("item_name") or raw.get("wanted_item") or title
    mat = raw.get("material_type")

    amt = raw.get("amount") or raw.get("desired_amount")
    try:
        desired_amount = float(amt) if amt is not None and str(amt).strip() != "" else None
    except:
        desired_amount = None

    img_path = raw.get("image_url") or raw.get("image_path")
    image_url = make_public_url(img_path) if img_path else None

    return RequestDetailOut(
        request_id=rid,
        title=title,
        wanted_item=wanted_item,
        item_type=raw.get("item_type"),     
        material_type=mat,
        desired_amount=desired_amount,
        description=raw.get("description"),
        image_url=image_url,
        username=raw.get("username"),
        status=raw.get("status") or "pending",
        is_auto_written=raw.get("is_auto_written", False), 
    )