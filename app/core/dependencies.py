from typing import Optional

from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer

from app.services.cache_service import CacheService, InMemoryCacheService
from app.services.facebook_ads import FacebookAdsService

# Create an OAuth2 scheme for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=True)

# Create an optional OAuth2 scheme for development
optional_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token", auto_error=False
)

# Placeholder token for development - sử dụng token dài hạn của Facebook
DEFAULT_DEV_TOKEN = "EAADzKQZAbcmEBO3LlIXHVSUAQu6pNLh4PmTcqM50zEJtZAZAp1SZBreZCpYVMwlWOgkvTgbpJdpZCVIc6P8EuQVwqeEeqk7tfoZCeSZCz7GGd0cGG0jRQF46VEVJLwWZCS9eFLCrJG6Qsm4mUDhK3IEw7XqnP8eGGDQFGDUNZAM7VXVk2tQcRZAYUhbMdWyZAfGNUvmZBrLyXJFh2YqkBT25y4sZD"

# Create a cache instance to be used by the Facebook service
cache_instance = InMemoryCacheService()


def get_cache_service() -> CacheService:
    """
    Dependency to get a cache service instance.

    Returns:
        CacheService: A cache service instance
    """
    return cache_instance


async def get_auth_token(
    request: Request,
    token: Optional[str] = Depends(optional_oauth2_scheme),
    authorization: Optional[str] = Header(None),
) -> str:
    """
    Lấy token xác thực từ nhiều nguồn khác nhau, ưu tiên theo thứ tự:
    1. Token từ OAuth2 scheme (Authorization header)
    2. Token từ query parameter 'token'
    3. Token mặc định cho development

    Returns:
        str: Token xác thực
    """
    # 1. Nếu có token từ OAuth2, sử dụng nó
    if token:
        return token

    # 2. Kiểm tra từ header Authorization
    if authorization and authorization.startswith("Bearer "):
        return authorization.replace("Bearer ", "")

    # 3. Kiểm tra từ query parameters
    token_param = request.query_params.get("token")
    if token_param:
        return token_param

    # 4. Sử dụng token mặc định cho development
    return DEFAULT_DEV_TOKEN


def get_facebook_service(
    token: str = Depends(get_auth_token),
) -> FacebookAdsService:
    """
    Dependency to get an instance of the FacebookAdsService.

    Args:
        token: Authentication token for Facebook API

    Returns:
        FacebookAdsService: An initialized Facebook Ads service instance
    """
    service = FacebookAdsService(cache_service=cache_instance)
    # Set token for the service if not already set
    service.default_token = token
    return service


# Placeholder function - implement proper token validation as needed
def get_placeholder_token():
    return DEFAULT_DEV_TOKEN
