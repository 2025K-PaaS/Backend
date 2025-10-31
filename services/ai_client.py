# services/ai_client.py
from typing import Any, Dict, Optional, List, Union 
import httpx
from core.config import settings
from fastapi import UploadFile

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

def _drop_none(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}

def _as_file_part(upload: UploadFile) -> tuple[str, bytes, str]:
    upload.file.seek(0)
    buf = upload.file.read()
    upload.file.seek(0)
    if not buf or len(buf) == 0:
        raise ValueError("업로드된 이미지가 비어 있습니다(0 bytes). 프론트의 multipart/form-data 및 필드명(image)을 확인하세요.")
    filename = upload.filename or "upload.png"
    content_type = getattr(upload, "content_type", None) or "application/octet-stream"
    return (filename, buf, content_type)

def analyze_image(image_file: UploadFile, username: str) -> Dict[str, Any]:
    # bytes로 고정해서 전송
    img_part = _as_file_part(image_file)
    files = {"image": img_part}
    data = {"username": username}

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
    analysis_id: Optional[str] = None,   
    title: Optional[str] = None,
    description: Optional[str] = None,
     amount: Optional[float | int | str] = None, 
    value: Optional[int] = None,
    username: Optional[str] = None,
    item_name: Optional[str] = None,
    item_type: Optional[str], 
    material_type: Optional[str] = None,
    matched_request_id: Optional[str] = None,
    image_path: Optional[str] = None, 

) -> Dict[str, Any]:
    amount_str: Optional[str] = None
    if amount is not None:
        amount_str = str(amount)

    payload = _drop_none({
        "analysis_id": analysis_id,
        "title": title,
        "description": description,
        "amount": amount_str,  
        "value": value,
        "username": username,
        "material_type": material_type,
        "item_name": item_name,
        "item_type": item_type, 
        "matched_request_id": matched_request_id,
        "image_path": image_path,
    })
    if analysis_id:                
        payload["analysis_id"] = analysis_id

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
    if username: params["username"] = username  
    if material_type: params["material_type"] = material_type
    if status: params["status"] = status

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

def create_request_on_ai(payload: Dict[str, Any], image: Optional[UploadFile] = None) -> Dict[str, Any]:
    url = f"{_base()}/requests/"
    with httpx.Client(timeout=20.0) as client:
        files = None

        if image:
            img_part = _as_file_part(image)
            files = {"image": img_part}

        data = {
            "item_name": str(payload.get("item_name", "")),
            "title": str(payload.get("item_name", "")),
            "amount": str(payload.get("amount", "")),
            "description": str(payload.get("description", "")),
            "username": str(payload.get("username", "")),
            "item_type":str(payload.get("item_type", "")),
            "image_path":str(payload.get("image_path", "")),
        }
        mt = payload.get("material_type")
        if mt is not None:
            data["material_type"] = str(mt)
        it = payload.get("item_type")
        if it is not None:
            data["item_type"] = str(it)

        r = client.post(url, headers=_headers(), data=data, files=files)
        print("🔥 AI 요청 응답 내용:", r.text)
        r.raise_for_status()
        return r.json()

# 모든 요청 목록 조회 (pending 등 상태별)
def get_all_requests(status: Optional[str] = None) -> List[Dict[str, Any]]:
    url = f"{_base()}/requests/all"
    params = {}
    if status:
        params["status"] = status

    with httpx.Client(timeout=15.0) as client:
        r = client.get(url, headers=_headers(), params=params)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and "requests" in data:
            return data["requests"]
        if isinstance(data, list):
            return data
        raise ValueError(f"AI 서버 응답 형식 오류: {type(data)}")
    
# 자원 기준 매칭 조회
def get_match_by_resource(resource_id: str) -> Dict[str, Any]:
    url = f"{_base()}/match/by_resource"
    with httpx.Client(timeout=15.0) as client:
        r = client.get(url, headers=_headers(), params={"resource_id": resource_id})
        r.raise_for_status()
        return _ensure_dict(r.json())

# 요청 기준 매칭 조회
def get_match_by_request(request_id: str) -> Dict[str, Any]:
    url = f"{_base()}/match/by_request"
    with httpx.Client(timeout=15.0) as client:
        r = client.get(url, headers=_headers(), params={"request_id": request_id})
        r.raise_for_status()
        return _ensure_dict(r.json())

# '수락' 또는 '거절'된 매칭 조회
def get_match_history(
    *,
    username: Optional[str] = None,
    resource_id: Optional[str] = None,
    request_id: Optional[str] = None,
    status: Optional[str] = None,      # "accepted" | "declined" (필터 안 쓰면 전체)
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    과거 수락/거절된 매칭 기록 조회
    """
    url = f"{_base()}/match/history"
    params: Dict[str, Any] = {"limit": limit, "offset": offset}
    if username:    params["username"]    = username
    if resource_id: params["resource_id"] = resource_id
    if request_id:  params["request_id"]  = request_id
    if status:      params["status"]      = status  # accepted | declined

    with httpx.Client(timeout=20.0) as client:
        r = client.get(url, headers=_headers(), params=params)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            if "items" in data and isinstance(data["items"], list):
                return data["items"]
            if "matches" in data and isinstance(data["matches"], list):
                return data["matches"]
        raise ValueError(f"AI 히스토리 응답 형식 오류: {type(data)}")

# 모든 자원 조회
def get_all_resources() -> List[Dict[str, Any]]:
    url = f"{_base()}/resources/all"
    with httpx.Client(timeout=20.0) as client:
        r = client.get(url, headers=_headers())
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and "resources" in data:
            return data["resources"]
        if isinstance(data, list):
            return data
        raise ValueError(f"AI 서버 응답 형식 오류: {type(data)}")

# 제안된 매칭 수락/거절
def confirm_match(resource_id: str, request_id: str, action: str) -> Dict[str, Any]:
    url = f"{_base()}/match/confirm"
    body = {"resource_id": resource_id, "request_id": request_id, "action": action}
    with httpx.Client(timeout=15.0) as client:
        r = client.post(url, headers={**_headers(), "Content-Type": "application/json"}, json=body)
        r.raise_for_status()
        return r.json()
    

# 수동으로 매칭 요청
def manual_match(resource_id: str, amount: str | int | float, username: str) -> Dict[str, Any]:
    url = f"{_base()}/match/manual"
    payload = {
        "resource_id": str(resource_id),
        "amount": str(amount),      
        "username": str(username),
    }
    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        r = client.post(url, headers={**_headers(), "Content-Type": "application/json"}, json=payload)
        print("🔥 AI 수동매칭 응답:", r.status_code, r.text)
        r.raise_for_status()
        return _ensure_dict(r.json())

