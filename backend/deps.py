from typing import Optional
from fastapi import Header, HTTPException

from backend.database import get_db


def get_api_key(x_api_key: Optional[str] = Header(None)) -> Optional[str]:
    return x_api_key


def require_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="OpenAI API key required. Pass it in the X-API-Key header."
        )
    return x_api_key
