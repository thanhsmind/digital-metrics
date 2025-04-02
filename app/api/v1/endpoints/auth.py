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
    TokenRefreshResponse,
    TokenValidationResponse,
)
from app.services.facebook.auth_service import AuthError, FacebookAuthService
from app.services.facebook.token_manager import TokenManager
from app.tasks.token_refresh import TokenRefreshTask
from app.utils.auth import internal_api_key_auth

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


@router.post("/facebook/refresh", response_model=TokenRefreshResponse)
async def refresh_facebook_token(
    token: str = Query(..., description="Facebook token to refresh")
):
    """
    Refresh Facebook access token

    Args:
        token: Facebook access token to refresh

    Returns:
        TokenRefreshResponse với thông tin về token mới
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
            return TokenRefreshResponse(
                success=False, message="Token could not be refreshed"
            )

        # Validate new token
        validation = await facebook_auth_service.validate_token(new_token)
        return TokenRefreshResponse(
            success=True,
            message="Token refreshed successfully",
            new_token=new_token,
            expires_at=validation.expires_at,
            is_valid=validation.is_valid,
        )
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


@router.post("/facebook/encrypt-tokens", response_model=Dict[str, Any])
async def encrypt_facebook_tokens():
    """
    Mã hóa tất cả token Facebook đã lưu trữ

    Hữu ích khi migrate từ hệ thống không mã hóa sang có mã hóa

    Returns:
        Thống kê số lượng token đã mã hóa
    """
    try:
        # Đếm số lượng token đã mã hóa
        encrypted_count = 0
        total_count = 0

        # Kiểm tra token chính
        current_token = await token_manager.load_token()
        if current_token:
            total_count += 1
            # Tải thông tin token hiện tại
            validation = await facebook_auth_service.validate_token(
                current_token
            )

            # Mã hóa và lưu token
            await token_manager.save_token(
                current_token,
                {
                    "expires_at": (
                        validation.expires_at.isoformat()
                        if validation.expires_at
                        else None
                    ),
                    "user_id": validation.user_id,
                    "scopes": validation.scopes,
                },
            )
            encrypted_count += 1

        # Tải tokens từ file
        if not hasattr(facebook_auth_service, "tokens_data"):
            facebook_auth_service._load_tokens()

        # Mã hóa user tokens
        if "user_tokens" in facebook_auth_service.tokens_data:
            for user_id, token_data in list(
                facebook_auth_service.tokens_data["user_tokens"].items()
            ):
                # Kiểm tra xem token đã mã hóa chưa
                if (
                    isinstance(token_data, dict)
                    and "encrypted" in token_data
                    and token_data["encrypted"]
                ):
                    continue

                # Lấy user token
                user_token = await facebook_auth_service._get_user_token(
                    user_id
                )
                if user_token:
                    total_count += 1
                    # Lưu lại với mã hóa
                    await facebook_auth_service._store_user_token(user_token)
                    encrypted_count += 1

        # Mã hóa page tokens
        if "page_tokens" in facebook_auth_service.tokens_data:
            for page_id, token_data in list(
                facebook_auth_service.tokens_data["page_tokens"].items()
            ):
                # Kiểm tra xem token đã mã hóa chưa
                if (
                    isinstance(token_data, dict)
                    and "encrypted" in token_data
                    and token_data["encrypted"]
                ):
                    continue

                # Lấy page token
                page_token = await facebook_auth_service._get_page_token(
                    page_id
                )
                if page_token:
                    total_count += 1
                    # Lưu lại với mã hóa
                    await facebook_auth_service._store_page_token(page_token)
                    encrypted_count += 1

        return {
            "success": True,
            "message": f"Encrypted {encrypted_count} of {total_count} tokens",
            "encrypted_count": encrypted_count,
            "total_count": total_count,
        }
    except Exception as e:
        logging.error(f"Error encrypting tokens: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error encrypting tokens: {str(e)}",
        )


@router.post(
    "/facebook/internal/scheduled-refresh", response_model=Dict[str, Any]
)
async def scheduled_refresh(
    hours_threshold: int = Query(
        24, description="Số giờ trước khi token hết hạn cần refresh"
    ),
    api_key: str = Depends(internal_api_key_auth),
):
    """
    Endpoint nội bộ được gọi bởi scheduler để refresh tất cả Facebook tokens sắp hết hạn.
    Endpoint này được bảo vệ bởi API key nội bộ.

    Args:
        hours_threshold: Số giờ trước khi token hết hạn sẽ được refresh
        api_key: API key cho internal endpoints

    Returns:
        Danh sách kết quả refresh cho mỗi token
    """
    try:
        # Kiểm tra cấu hình Facebook API
        if (
            not facebook_auth_service.app_id
            or not facebook_auth_service.app_secret
        ):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Facebook API credentials are not properly configured",
            )

        # Gọi token manager để refresh tokens sắp hết hạn
        results = await token_manager.refresh_expiring_tokens(hours_threshold)

        # Tính toán thống kê
        success_count = sum(1 for r in results if r.get("success", False))
        error_count = len(results) - success_count

        # Trả về kết quả
        return {
            "success": success_count > 0,
            "message": f"Refreshed {success_count} tokens, {error_count} errors",
            "total_tokens": len(results),
            "success_count": success_count,
            "error_count": error_count,
            "results": results,
        }
    except Exception as e:
        logging.error(f"Error in scheduled refresh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during scheduled refresh: {str(e)}",
        )
