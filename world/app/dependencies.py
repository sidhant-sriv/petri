from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from .core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key")


def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == settings.API_KEY:
        return api_key
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
