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
        raise ValueError("file too large (>5MB)")

def _save_local_copy(file: UploadFile) -> str:
    _ensure_dir()
    name = _unique_name(file.filename)
    path = UPLOAD_DIR / name
    # reset to start to be safe
    file.file.seek(0)
    with open(path, "wb") as f:
        f.write(file.file.read())
    # reset again for re-use in requests
    file.file.seek(0)
    return str(path)

def call_ai_and_save(db: Session, username: str, file: UploadFile) -> Analysis:
    # size check
    _check_size(file)

    # local backup
    local_path = _save_local_copy(file)

    files = {"image": (file.filename or "upload.bin", file.file, file.content_type or "application/octet-stream")}
    data = {"username": username}
    headers = {"Authorization": f"Bearer {settings.SERVER_ONLY_AI_API_KEY}"}

    # upstream call
    resp = requests.post(settings.AI_ANALYSIS_URL, headers=headers, files=files, data=data, timeout=20)
    resp.raise_for_status()
    j = resp.json()

    anal = Analysis(
        ai_analysis_id=j["analysis_id"],
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
