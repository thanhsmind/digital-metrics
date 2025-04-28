import json
import logging
import os
from datetime import datetime
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
from jose import JOSEError, jwe
from jose.constants import ALGORITHMS

from app.core.config import settings
from app.models.auth import (
    FacebookPageToken,
    FacebookUserToken,
    TokenPermissionCheckResponse,
    TokenRefreshResponse,
    TokenValidationResponse,
)
from app.services.facebook.auth_service import AuthError, FacebookAuthService
from app.services.facebook.token_manager import TokenManager
from app.tasks.token_refresh import TokenRefreshTask
from app.utils.auth import internal_api_key_auth
from app.utils.encryption import TokenEncryption

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
    Đảm bảo rằng tất cả các token (user, page, business) đều được mã hóa
    bằng giải thuật JWE trước khi lưu trữ.

    Returns:
        Thống kê chi tiết về số lượng token đã mã hóa và loại token
    """
    try:
        print("\n\n===== ENCRYPT TOKENS ENDPOINT CALLED =====")

        # Temporarily set logging to DEBUG level for encryption diagnostics
        original_level = logging.getLogger().level
        logging.getLogger().setLevel(logging.DEBUG)
        logging.info("Starting token encryption process with DEBUG logging")

        # Đếm số lượng token đã mã hóa theo loại
        result = {
            "main_token": {"total": 0, "encrypted": 0},
            "user_tokens": {"total": 0, "encrypted": 0},
            "page_tokens": {"total": 0, "encrypted": 0},
            "business_tokens": {"total": 0, "encrypted": 0},
        }

        # Kiểm tra token chính
        current_token = await token_manager.load_token()
        if current_token:
            result["main_token"]["total"] += 1
            print(f"Main token loaded, length: {len(current_token)}")

            # Tải thông tin token hiện tại
            validation = await facebook_auth_service.validate_token(
                current_token
            )

            # Mã hóa token với TokenEncryption class (JWE or BASE64 fallback)
            encrypted_token, is_encrypted = TokenEncryption.encrypt_if_needed(
                current_token
            )

            if is_encrypted:
                print(
                    f"Token encrypted successfully, new length: {len(encrypted_token)}"
                )
                if encrypted_token.startswith(TokenEncryption.JWE_PREFIX):
                    print("Token encrypted with JWE method")
                elif encrypted_token.startswith(TokenEncryption.BASE64_PREFIX):
                    print("Token encrypted with BASE64 method (fallback)")
            else:
                print("Failed to encrypt token")

            # Tạo data cho token
            token_data = {
                "expires_at": (
                    validation.expires_at.isoformat()
                    if validation.expires_at
                    else None
                ),
                "user_id": validation.user_id,
                "scopes": validation.scopes,
                "access_token": encrypted_token,
                "encrypted": is_encrypted,
                "updated_at": datetime.now().isoformat(),
            }

            # Lưu token trực tiếp vào file thay vì qua save_token
            try:
                token_file = settings.FACEBOOK_TOKEN_FILE
                # Đảm bảo thư mục tồn tại
                os.makedirs(os.path.dirname(token_file), exist_ok=True)

                with open(token_file, "w") as f:
                    json.dump(token_data, f, indent=2)

                result["main_token"]["encrypted"] += 1 if is_encrypted else 0
                print(f"Token file saved at: {token_file}")

                if encrypted_token.startswith(TokenEncryption.JWE_PREFIX):
                    logging.info("Main token encrypted with JWE")
                elif encrypted_token.startswith(TokenEncryption.BASE64_PREFIX):
                    logging.info(
                        "Main token encrypted with BASE64 (fallback solution)"
                    )
            except Exception as e:
                print(f"Error saving token file: {str(e)}")
                logging.error(f"Error saving encoded main token: {str(e)}")

        print("===== ENCRYPT TOKENS ENDPOINT COMPLETE =====\n\n")

        # Restore original logging level
        logging.info(
            "Token encryption process complete, restoring original logging level"
        )
        logging.getLogger().setLevel(original_level)

        # Tính tổng số token đã mã hóa
        total_tokens = (
            result["main_token"]["total"]
            + result["user_tokens"]["total"]
            + result["page_tokens"]["total"]
            + result["business_tokens"]["total"]
        )
        encrypted_tokens = (
            result["main_token"]["encrypted"]
            + result["user_tokens"]["encrypted"]
            + result["page_tokens"]["encrypted"]
            + result["business_tokens"]["encrypted"]
        )

        return {
            "success": True,
            "message": f"Encoded {encrypted_tokens} of {total_tokens} tokens",
            "total_tokens": total_tokens,
            "encrypted_tokens": encrypted_tokens,
            "details": result,
        }
    except Exception as e:
        print(f"ERROR in encrypt_facebook_tokens: {str(e)}")
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


@router.get("/facebook/business-token", response_model=TokenValidationResponse)
async def get_business_token(
    business_id: str = Query(..., description="ID của Facebook Business"),
    user_token: str = Query(
        ..., description="User access token với quyền business_management"
    ),
):
    """
    Lấy token cho Business Facebook cụ thể.

    Args:
        business_id: ID của Facebook Business
        user_token: User access token với quyền business_management

    Returns:
        TokenValidationResponse: Thông tin token và trạng thái
    """
    try:
        # Lấy business token từ storage nếu có
        existing_token = await token_manager.get_business_token(business_id)

        if existing_token:
            # Validate token đã lưu
            validation = await facebook_auth_service.validate_token(
                existing_token
            )
            if validation.is_valid and (
                not validation.expires_at
                or validation.expires_at > datetime.now()
            ):
                # Token hiện tại còn hiệu lực, trả về
                return validation

        # Nếu không có token hoặc token không còn hiệu lực, lấy token mới
        business_token = await facebook_auth_service.get_business_access_token(
            user_token, business_id
        )

        if not business_token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy Business Token cho business_id: {business_id}",
            )

        # Lưu business token vào storage
        await token_manager.save_business_token(
            business_id,
            business_token.access_token,
            {
                "app_id": business_token.app_id,
                "expires_at": (
                    business_token.expires_at.isoformat()
                    if business_token.expires_at
                    else None
                ),
                "scopes": business_token.scopes,
            },
        )

        # Validate và trả về thông tin token
        return await facebook_auth_service.validate_token(
            business_token.access_token
        )

    except AuthError as e:
        logging.error(
            f"Authentication error: {e.message} (code: {e.error_code})"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": f"Authentication error: {e.message}",
                "error_code": e.error_code,
            },
        )
    except Exception as e:
        logging.error(f"Error getting business token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting business token: {str(e)}",
        )


@router.post("/facebook/extend-permissions")
async def extend_token_permissions(
    token: str = Query(..., description="Token cần mở rộng quyền"),
    permissions: str = Query(
        ..., description="Danh sách quyền cần thêm, phân tách bằng dấu phẩy"
    ),
):
    """
    Mở rộng quyền cho token hiện có.

    Args:
        token: Token cần mở rộng quyền
        permissions: Danh sách quyền cần thêm, phân tách bằng dấu phẩy (ví dụ: business_management,ads_management)

    Returns:
        Dict chứa URL xác thực để hoàn thành quá trình mở rộng quyền
    """
    try:
        # Chuyển đổi chuỗi permissions thành list
        permission_list = [
            p.strip() for p in permissions.split(",") if p.strip()
        ]

        if not permission_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cần cung cấp ít nhất một quyền để mở rộng",
            )

        # Lấy URL xác thực để mở rộng quyền
        auth_url = await facebook_auth_service.extend_token_permissions(
            token, permission_list
        )

        if not auth_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể tạo URL xác thực để mở rộng quyền",
            )

        return {
            "success": True,
            "message": "Cần xác thực để mở rộng quyền token",
            "authentication_url": auth_url,
            "instructions": "Truy cập URL xác thực để cấp quyền bổ sung, sau đó sử dụng /auth/facebook/callback để hoàn thành quá trình",
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
            },
        )
    except Exception as e:
        logging.error(f"Error extending token permissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extending token permissions: {str(e)}",
        )


@router.get(
    "/facebook/check-permissions", response_model=TokenPermissionCheckResponse
)
async def check_token_permissions(
    token: str = Query(..., description="Token cần kiểm tra"),
    required_permissions: str = Query(
        ..., description="Danh sách quyền cần kiểm tra, phân tách bằng dấu phẩy"
    ),
):
    """
    Kiểm tra xem token có đủ quyền cho hoạt động cụ thể không.

    Args:
        token: Token cần kiểm tra
        required_permissions: Danh sách quyền cần kiểm tra, phân tách bằng dấu phẩy
                             (ví dụ: business_management,ads_management)

    Returns:
        TokenPermissionCheckResponse: Kết quả kiểm tra quyền
    """
    try:
        # Chuyển đổi chuỗi permissions thành list
        permission_list = [
            p.strip() for p in required_permissions.split(",") if p.strip()
        ]

        if not permission_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cần cung cấp ít nhất một quyền để kiểm tra",
            )

        # Kiểm tra quyền của token
        result = await token_manager.check_token_permissions(
            token, permission_list
        )
        return result

    except Exception as e:
        logging.error(f"Error checking token permissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking token permissions: {str(e)}",
        )


@router.post("/facebook/re-encrypt-tokens", response_model=Dict[str, Any])
async def re_encrypt_facebook_tokens(
    force: bool = Query(
        False,
        description="Cưỡng chế mã hóa lại cả những token đã mã hóa trước đó",
    ),
    api_key: str = Depends(internal_api_key_auth),
):
    """
    Endpoint nội bộ để mã hóa lại tất cả token Facebook bằng JWE

    Chuyển đổi token từ mã hóa tạm thời (Base64) sang mã hóa JWE an toàn hơn.
    Endpoint này được bảo vệ bởi API key nội bộ.

    Args:
        force: Nếu True, mã hóa lại cả những token đã mã hóa trước đó
        api_key: API key cho internal endpoints

    Returns:
        Thống kê chi tiết về số lượng token đã mã hóa và loại token
    """
    try:
        logging.info(f"Starting token re-encryption process (force={force})")

        # Đếm số lượng token đã mã hóa theo loại
        result = {
            "main_token": {"total": 0, "encrypted": 0, "already_jwe": 0},
            "user_tokens": {"total": 0, "encrypted": 0, "already_jwe": 0},
            "page_tokens": {"total": 0, "encrypted": 0, "already_jwe": 0},
            "business_tokens": {"total": 0, "encrypted": 0, "already_jwe": 0},
        }

        # Re-encrypt main token
        token_file = settings.FACEBOOK_TOKEN_FILE
        if os.path.exists(token_file):
            try:
                with open(token_file, "r") as f:
                    data = json.load(f)

                result["main_token"]["total"] += 1

                if "access_token" in data:
                    token = data["access_token"]

                    # Skip if already JWE encrypted and not forcing re-encryption
                    if (
                        token.startswith(TokenEncryption.JWE_PREFIX)
                        and not force
                    ):
                        logging.info(
                            "Main token already JWE encrypted, skipping"
                        )
                        result["main_token"]["already_jwe"] += 1
                    else:
                        # Decrypt token if needed
                        if TokenEncryption.is_encrypted(token):
                            decrypted_token = TokenEncryption.decrypt_token(
                                token
                            )
                            if not decrypted_token:
                                logging.error(
                                    "Failed to decrypt main token for re-encryption"
                                )
                                raise ValueError("Failed to decrypt token")
                        else:
                            decrypted_token = token

                        # Re-encrypt with JWE
                        secret_key = TokenEncryption._get_properly_sized_key()
                        try:
                            jwe_token = jwe.encrypt(
                                decrypted_token,
                                secret_key,
                                algorithm=ALGORITHMS.DIR,
                                encryption=ALGORITHMS.A256GCM,
                            )
                            encrypted_token = (
                                f"{TokenEncryption.JWE_PREFIX}{jwe_token}"
                            )

                            # Update token data
                            data["access_token"] = encrypted_token
                            data["encrypted"] = True
                            data["updated_at"] = datetime.now().isoformat()

                            # Save updated token
                            with open(token_file, "w") as f:
                                json.dump(data, f, indent=2)

                            logging.info(
                                "Main token successfully re-encrypted with JWE"
                            )
                            result["main_token"]["encrypted"] += 1
                        except Exception as e:
                            logging.error(
                                f"Failed to re-encrypt main token with JWE: {str(e)}"
                            )
                            raise
            except Exception as e:
                logging.error(f"Error re-encrypting main token: {str(e)}")

        # Tính tổng số token đã mã hóa
        total_tokens = result["main_token"]["total"]
        encrypted_tokens = result["main_token"]["encrypted"]
        already_jwe = result["main_token"]["already_jwe"]

        logging.info(
            f"Token re-encryption complete: {encrypted_tokens} re-encrypted, {already_jwe} were already JWE encrypted"
        )

        return {
            "success": True,
            "message": f"Re-encrypted {encrypted_tokens} tokens with JWE, {already_jwe} were already JWE encrypted",
            "total_tokens": total_tokens,
            "encrypted_tokens": encrypted_tokens,
            "already_jwe_encrypted": already_jwe,
            "details": result,
        }
    except Exception as e:
        logging.error(f"Error in token re-encryption: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error re-encrypting tokens: {str(e)}",
        )
