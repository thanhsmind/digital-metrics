import logging
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
    status,
)
from fastapi.responses import JSONResponse, RedirectResponse

from app.models.auth import (
    FacebookPageToken,
    FacebookUserToken,
    TokenValidationResponse,
)
from app.services.facebook.auth_service import AuthError, FacebookAuthService
from app.services.facebook.token_manager import TokenManager
from app.tasks.token_refresh import TokenRefreshTask

router = APIRouter()
facebook_auth_service = FacebookAuthService()
token_manager = TokenManager()
token_refresh_task = TokenRefreshTask()


@router.get("/facebook/callback")
async def facebook_callback(
    code: str = Query(..., description="Authorization code from Facebook"),
    state: Optional[str] = Query(
        None, description="State parameter for CSRF protection"
    ),
):
    """
    Callback endpoint nhận code từ Facebook OAuth

    Args:
        code: Authorization code từ Facebook
        state: State parameter để xác minh request

    Returns:
        Token information
    """
    try:
        # Kiểm tra cấu hình Facebook API
        if (
            not facebook_auth_service.app_id
            or not facebook_auth_service.app_secret
        ):
            logging.error("Facebook credentials missing in environment")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "message": "Facebook API credentials are not properly configured.",
                    "setup_instructions": "1. Cập nhật file .env với FACEBOOK_APP_ID và FACEBOOK_APP_SECRET từ Facebook Developer Console\n"
                    "2. Đảm bảo URL Callback trong ứng dụng Facebook khớp với FACEBOOK_REDIRECT_URI trong .env\n"
                    "3. Khởi động lại ứng dụng sau khi cập nhật .env",
                },
            )

        token = await facebook_auth_service.exchange_code_for_token(code)

        # Trong production, nên redirect đến frontend với token hoặc session
        # Nhưng ở đây chúng ta trả về token info để dễ test
        return {
            "message": "Authentication successful",
            "user_id": token.user_id,
            "token_type": token.token_type,
            "expires_at": token.expires_at,
            "scopes": token.scopes,
        }
    except AuthError as e:
        logging.error(
            f"Authentication error: {e.message} (code: {e.error_code})"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": f"Authentication error: {e.message}",
                "error_code": e.error_code,
                "help": "Nếu lỗi liên quan đến cấu hình, hãy kiểm tra file .env của bạn.",
            },
        )
    except Exception as e:
        logging.error(f"Unexpected error during authentication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during authentication: {str(e)}",
        )


@router.get("/facebook/validate", response_model=TokenValidationResponse)
async def validate_facebook_token(
    token: str = Query(..., description="Facebook access token to validate")
):
    """
    Validate Facebook access token

    Args:
        token: Facebook access token

    Returns:
        TokenValidationResponse với thông tin về token
    """
    try:
        return await facebook_auth_service.validate_token(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating token: {str(e)}",
        )


@router.get("/facebook/user-pages", response_model=List[FacebookPageToken])
async def get_user_pages(
    token: str = Query(..., description="Facebook user access token")
):
    """
    Lấy danh sách pages mà user có quyền truy cập

    Args:
        token: Facebook user access token

    Returns:
        List FacebookPageToken objects
    """
    try:
        return await facebook_auth_service.get_user_pages(token)
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Facebook auth error: {e.message}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting user pages: {str(e)}",
        )


@router.post("/facebook/refresh", response_model=Dict[str, Any])
async def refresh_facebook_token(
    token: str = Query(..., description="Facebook token to refresh")
):
    """
    Refresh Facebook access token

    Args:
        token: Facebook access token to refresh

    Returns:
        New token information
    """
    try:
        # Kiểm tra cấu hình Facebook API
        if (
            not facebook_auth_service.app_id
            or not facebook_auth_service.app_secret
        ):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Facebook API credentials are not properly configured. Set FACEBOOK_APP_ID and FACEBOOK_APP_SECRET in environment variables.",
            )

        new_token = await facebook_auth_service.refresh_token(token)
        if not new_token:
            return {"success": False, "message": "Token could not be refreshed"}

        # Validate new token
        validation = await facebook_auth_service.validate_token(new_token)
        return {
            "success": True,
            "new_token": new_token,
            "expires_at": validation.expires_at,
            "is_valid": validation.is_valid,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error refreshing token: {str(e)}",
        )


@router.post("/facebook/refresh-token", response_model=Dict[str, Any])
@router.get("/facebook/refresh-token", response_model=Dict[str, Any])
async def force_refresh_facebook_token(background_tasks: BackgroundTasks):
    """
    Force refresh Facebook tokens và khởi động background task

    Args:
        background_tasks: FastAPI background tasks runner

    Returns:
        Status và thông tin refresh
    """
    try:
        # Kiểm tra cấu hình Facebook API
        if (
            not facebook_auth_service.app_id
            or not facebook_auth_service.app_secret
        ):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Facebook API credentials are not properly configured. Set FACEBOOK_APP_ID and FACEBOOK_APP_SECRET in environment variables.",
            )

        # Gọi token manager để refresh tất cả token trong storage
        success = await token_manager.refresh_all_tokens()

        if success:
            logging.info("Token refresh successful")
            # Khởi động background task để kiểm tra token định kỳ
            await token_refresh_task.start_background_task(background_tasks)

            return {
                "success": True,
                "message": "Token refreshed successfully",
                "next_check": "24 hours",
            }
        else:
            logging.warning("Token refresh failed, generating new OAuth URL")
            # Nếu không thể làm mới, cung cấp link OAuth mới
            auth_url_data = facebook_auth_service.get_authorization_url()
            return {
                "success": False,
                "message": "Token is invalid and could not be refreshed, please complete OAuth flow",
                "authorization_url": auth_url_data["authorization_url"],
                "state": auth_url_data["state"],
            }
    except Exception as e:
        logging.error(f"Error in force_refresh_facebook_token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error refreshing token: {str(e)}",
        )
