# routers/resources.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from core.deps import get_db, get_current_user
from services.resource_service import auto_create_from_image, list_by_username, list_all_resources
from schemas.resource import (
    ResourceCreateOut,
    MatchedRequest,
    ResourceListOut,
    ResourceRow,
)

router = APIRouter(prefix="/resources", tags=["resources"])

@router.post("", response_model=ResourceCreateOut)
def create_resource(
    image: UploadFile = File(...),
    title: str | None = Form(None),
    description: str | None = Form(None),
    amount: float | None = Form(None),
    unit: str | None = Form(None),
    value: int | None = Form(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        analysis, created = auto_create_from_image(
            user=current_user,
            image_file=image,
            title=title,
            description=description,
            amount=amount,
            unit=unit,
            value=value,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    resp = created

    return ResourceCreateOut(
        resource_id=resp.get("resource_id"),
        status=resp.get("status", "registered"),
        message=resp.get("message", "자원이 등록되었습니다."),
        matched_requests=[
            MatchedRequest(
                request_id=m.get("request_id"),
                wanted_item=m.get("wanted_item"),
                material_type=m.get("material_type"),
                desired_amount=m.get("desired_amount"),
                unit=m.get("unit"),
            )
            for m in (resp.get("matched_requests") or [])
        ],
    )

# 로그인한 사용자의 자원 목록 조회
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
                title=r.get("title"),
                material_type=r.get("material_type"),
                amount=r.get("amount"),
                unit=r.get("unit"),
                value=r.get("value"),
                status=r.get("status", "registered"),
            )
            for r in rows
        ],
        total=total,
    )

# 전체 자원 목록 조회 - 인증 불필요
@router.get("/all", response_model=ResourceListOut)
def list_all(
    material_type: str | None = Query(None, description="자원 종류 필터 (예: 플라스틱, 데님 등)"),
    status: str | None = Query(None, description="상태 필터 (registered, matched, in_progress 등)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    전체 자원 목록 조회 (로그인 필요 없음)
    - 내부적으로 모든 사용자에 대해 AI 서버의 /resources/user/{username}을 호출하여 집계
    """
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
                title=r.get("title"),
                material_type=r.get("material_type"),
                amount=r.get("amount"),
                unit=r.get("unit"),
                value=r.get("value"),
                status=r.get("status"),
            )
            for r in rows
        ],
        total=total,
    )