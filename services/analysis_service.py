# services/analysis_service.py
import os
from uuid import uuid4
from pathlib import Path
import requests
from fastapi import UploadFile
from sqlalchemy.orm import Session
from core.config import settings
from models.analysis import Analysis

UPLOAD_DIR = Path("uploads/analysis")
MAX_SIZE = 5 * 1024 * 1024  # 5MB

AI_ANALYZE_URL = f"{settings.AI_API_BASE.rstrip('/')}/analysis/image"
LOCAL_ANALYSIS_PREFIX = "anl_local_" 

def _ensure_dir() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def _unique_name(orig: str | None) -> str:
    ext = ""
    if orig and "." in orig:
        ext = "." + orig.rsplit(".", 1)[-1].lower()
    return f"{uuid4().hex}{ext or '.bin'}"

def _check_size(uf: UploadFile) -> None:
    pos = uf.file.tell()
    uf.file.seek(0, os.SEEK_END)
    size = uf.file.tell()
    uf.file.seek(pos)
    if size > MAX_SIZE:
        raise ValueError("파일 크기가 너무 큽니다. (5MB 초과)")

def _save_local_copy(file: UploadFile) -> str:
    _ensure_dir()
    name = _unique_name(file.filename)
    path = UPLOAD_DIR / name
    file.file.seek(0)
    with open(path, "wb") as f:
        f.write(file.file.read())
    file.file.seek(0)
    return str(path)

def call_ai_and_save(db: Session, username: str, file: UploadFile) -> Analysis:
    _check_size(file)
    local_path = _save_local_copy(file)

    files = {
        "file": (
            file.filename or "upload.bin",
            file.file,
            file.content_type or "application/octet-stream",
        )
    }
    data = {"username": username}

    headers = {"Accept": "application/json"}
    if settings.SERVER_ONLY_AI_API_KEY:
        headers["Authorization"] = f"Bearer {settings.SERVER_ONLY_AI_API_KEY}"

    resp = requests.post(
        AI_ANALYZE_URL,
        headers=headers,
        files=files,
        data=data,
        timeout=20,
    )
    resp.raise_for_status()
    j = resp.json()

    ai_id = j.get("analysis_id")
    if not ai_id:
        ai_id = f"{LOCAL_ANALYSIS_PREFIX}{uuid4().hex}"

    anal = Analysis(
        ai_analysis_id=ai_id,          
        username=username,
        detected_item=j.get("detected_item"),
        material_type=j.get("material_type"),
        suggested_title=j.get("suggested_title"),
        image_path=local_path,
    )
    db.add(anal)
    db.commit()
    db.refresh(anal)
    return anal
