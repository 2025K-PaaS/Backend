# core/utils.py
from core.config import settings

def make_public_url(path: str | None, base_url: str | None = None) -> str | None:
    if not path:
        return None
    if path.startswith(("http://", "https://")):
        return path
    base = (base_url or settings.PUBLIC_BASE_URL or "").rstrip("/")
    return f"{base}/{path.lstrip('/')}" if base else f"/{path.lstrip('/')}"

def make_ai_url(path: str | None) -> str | None:
    if not path:
        return None
    if path.startswith(("http://", "https://")):
        return path
    return f"{settings.AI_API_BASE.rstrip('/')}/{path.lstrip('/')}"