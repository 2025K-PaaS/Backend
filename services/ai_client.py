# services/ai_client.py
from typing import Any, Dict, Optional, List, Union 
import httpx
from core.config import settings

def _ensure_dict(data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Dict[str, Any]:
    # AI 응답과 맞추기 위한 함수
    while isinstance(data, list):
        if not data:         
            return {}
        data = data[0]      
    return data              

def _headers() -> Dict[str, str]:
    h = {"Accept": "application/json"}
    if settings.SERVER_ONLY_AI_API_KEY:
        h["Authorization"] = f"Bearer {settings.SERVER_ONLY_AI_API_KEY}"
    return h

def _base() -> str:
    return settings.AI_API_BASE.rstrip("/")

def analyze_image(image_file, username: str) -> Dict[str, Any]:
    files = {
        "file": (
            image_file.filename,
            image_file.file,
            getattr(image_file, "content_type", None) or "application/octet-stream",
        )
    }

    data = {"username": username}
    image_file.file.seek(0)

    with httpx.Client(timeout=30.0) as client:
        r = client.post(
            f"{_base()}/analysis/image",
            headers=_headers(),
            files=files,
            data=data,
        )
        r.raise_for_status()
        return r.json()

def register_resource(
    *,
    analysis_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    amount: Optional[float] = None,
    unit: Optional[str] = None,
    value: Optional[int] = None,
    username: Optional[str] = None,  
) -> Dict[str, Any]:
    payload = {
        "analysis_id": analysis_id,
        "title": title,
        "description": description,
        "amount": amount,
        "unit": unit,
        "value": value,
        "username": username,  
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    with httpx.Client(timeout=30.0) as client:
        r = client.post(
            f"{_base()}/resources", 
            headers={**_headers(), "Content-Type": "application/json"},
            json=payload,
        )
        print("[DEBUG AI RESPONSE]", r.status_code, r.text)  
        r.raise_for_status()
        return _ensure_dict(r.json())

def list_resource(
    *,
    username: Optional[str] = None,
    material_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {"limit": limit, "offset": offset}
    if material_type:
        params["material_type"] = material_type
    if status:
        params["status"] = status

    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        url = f"{_base()}/resources/user/{username}/"
        r = client.get(url, headers=_headers(), params=params)
        print("GET", url, params, "=>", r.status_code)
        if r.status_code == 404:
            url2 = f"{_base()}/resources/user/{username}"
            r = client.get(url2, headers=_headers(), params=params)
            print("FALLBACK GET", url2, params, "=>", r.status_code)
      
        if r.status_code in (307, 308):
            loc = r.headers.get("Location")
            if loc:
                print("REDIRECT to", loc)
                r = client.get(loc, headers=_headers())

        r.raise_for_status()

        try:
            data = r.json()
        except Exception as e:
            raise ValueError(f"AI 서버 응답 파싱 실패: {e}")

        if isinstance(data, list):
            return {"resources": data, "total": len(data)}
        if isinstance(data, dict):
            if "resources" not in data and "items" in data:
                return {"resources": data.get("items") or [], "total": data.get("count") or 0}
            if "resources" in data and "total" not in data:
                data["total"] = len(data.get("resources") or [])
            return data

        raise ValueError(f"AI 서버 응답 형식 오류: {type(data)}")
    

def create_request_on_ai(payload: Dict[str, Any]) -> Dict[str, Any]:
    with httpx.Client(timeout=20.0) as client:
        r = client.post(
            f"{_base()}/requests/",
            headers={**_headers(), "Content-Type": "application/json"},
            json=payload,
        )
        r.raise_for_status()
        data = r.json()

        if isinstance(data, list):
            return {"request_id": data[0].get("request_id"), "status": data[0].get("status"), "message": data[0].get("message")}
        return data