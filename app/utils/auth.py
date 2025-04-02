from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings

# Định nghĩa header cho API key
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def internal_api_key_auth(api_key: str = Security(API_KEY_HEADER)):
    """
    Xác thực API key cho internal endpoints

    Args:
        api_key: API key được truyền qua header X-API-Key

    Returns:
        API key nếu hợp lệ

    Raises:
        HTTPException: Nếu không có API key hoặc API key không hợp lệ
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "APIKey"},
        )

    if api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "APIKey"},
        )

    return api_key
