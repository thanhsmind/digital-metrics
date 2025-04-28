import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from facebook_business.exceptions import FacebookRequestError

from app.core.config import settings
from app.models.auth import (
    FacebookBusinessToken,
    FacebookUserToken,
    TokenPermissionCheckResponse,
    TokenValidationResponse,
)
from app.services.facebook.auth_service import FacebookAuthService
from app.utils.encryption import TokenEncryption


class TokenManager:
    """Quản lý lưu trữ token và cập nhật tự động"""

    def __init__(self):
        self.auth_service = FacebookAuthService()
        self.token_file = settings.FACEBOOK_TOKEN_FILE
        # Đảm bảo thư mục tồn tại
        self._ensure_token_dir_exists()

    def _ensure_token_dir_exists(self):
        """Đảm bảo thư mục lưu trữ token tồn tại"""
        os.makedirs(os.path.dirname(self.token_file), exist_ok=True)

    async def get_all_page_ids_for_user(self, user_id: str) -> List[str]:
        """Lấy danh sách các page ID liên kết với user"""
        if not hasattr(self.auth_service, "tokens_data"):
            # Reload tokens từ file nếu cần
            self.auth_service._load_tokens()

        if (
            "user_pages" in self.auth_service.tokens_data
            and user_id in self.auth_service.tokens_data["user_pages"]
        ):
            return self.auth_service.tokens_data["user_pages"][user_id]
        return []

    async def load_token(self) -> Optional[str]:
        """Tải token từ file hoặc từ settings"""
        # Kiểm tra FACEBOOK_APP_ID và FACEBOOK_APP_SECRET đã được thiết lập chưa
        if not settings.FACEBOOK_APP_ID or not settings.FACEBOOK_APP_SECRET:
            logging.warning(
                "FACEBOOK_APP_ID hoặc FACEBOOK_APP_SECRET chưa được cấu hình"
            )
            return None

        # Ưu tiên dùng token từ settings
        if settings.FACEBOOK_ACCESS_TOKEN:
            logging.info("Using access token from environment settings")
            return settings.FACEBOOK_ACCESS_TOKEN

        # Nếu không có, thử đọc từ file
        try:
            if os.path.exists(self.token_file):
                logging.info(
                    f"Token file found at {self.token_file}, loading token"
                )
                with open(self.token_file, "r") as f:
                    data = json.load(f)

                    # Kiểm tra token đã mã hóa hay chưa
                    if "encrypted" in data and data["encrypted"]:
                        if "access_token" in data:
                            # Kiểm tra xem có phải format BASE64 không
                            token = data["access_token"]
                            if token.startswith(TokenEncryption.BASE64_PREFIX):
                                logging.debug(
                                    "Found BASE64 encoded token (temporary solution)"
                                )
                            elif token.startswith(TokenEncryption.JWE_PREFIX):
                                logging.debug("Found JWE encrypted token")

                            # Giải mã token (supports both JWE and BASE64)
                            decrypted_token = TokenEncryption.decrypt_token(
                                token
                            )

                            if decrypted_token:
                                logging.debug("Token decryption successful")
                                return decrypted_token
                            else:
                                logging.error(
                                    "Failed to decrypt token from file, attempting to re-encrypt"
                                )
                                # Try to load a token from alternate sources
                                alt_token = self._handle_decryption_failure()
                                if alt_token:
                                    return alt_token
                    else:
                        # Token chưa mã hóa
                        if "access_token" in data:
                            logging.debug("Using unencrypted token from file")
                            return data["access_token"]
                        else:
                            logging.warning(
                                "Token file exists but does not contain access_token field"
                            )
            else:
                logging.warning(f"Token file {self.token_file} does not exist")
        except json.JSONDecodeError as e:
            logging.error(f"Token file contains invalid JSON: {str(e)}")
            # Try to recreate the token file if it's corrupted
            try:
                if settings.FACEBOOK_ACCESS_TOKEN:
                    logging.info("Recreating token file from environment token")
                    token = settings.FACEBOOK_ACCESS_TOKEN
                    await self.save_token(token)
                    return token
            except Exception as save_error:
                logging.error(
                    f"Failed to recreate token file: {str(save_error)}"
                )
        except Exception as e:
            logging.error(f"Error loading token from file: {str(e)}")

        logging.warning("No token available from environment or file")
        return None

    def _handle_decryption_failure(self) -> Optional[str]:
        """
        Xử lý trường hợp giải mã token thất bại

        Returns:
            Token từ nguồn khác hoặc None nếu không tìm thấy
        """
        # If token decryption failed, try to find a token from other sources
        logging.info(
            "Attempting to find alternate token source after decryption failure"
        )

        # Check if we have an environment token
        if settings.FACEBOOK_ACCESS_TOKEN:
            logging.info(
                "Using Facebook token from environment after decryption failure"
            )
            return settings.FACEBOOK_ACCESS_TOKEN

        # We could add more fallback methods here in the future
        return None

    async def save_token(self, token: str, token_data: Dict = None):
        """Lưu token vào file với mã hóa"""
        try:
            data = token_data or {}

            # Mã hóa token trước khi lưu, sử dụng encrypt_if_needed để tránh mã hóa lại
            encrypted_token, is_encrypted = TokenEncryption.encrypt_if_needed(
                token
            )
            if encrypted_token:
                data["access_token"] = encrypted_token
                data["encrypted"] = is_encrypted
                if is_encrypted:
                    if encrypted_token.startswith(TokenEncryption.JWE_PREFIX):
                        logging.info(
                            "Token JWE encrypted successfully before saving"
                        )
                    elif encrypted_token.startswith(
                        TokenEncryption.BASE64_PREFIX
                    ):
                        logging.info(
                            "Token BASE64 encoded before saving (fallback method)"
                        )
                else:
                    logging.warning(
                        "Failed to encrypt token, saving unencrypted"
                    )
            else:
                # Fallback khi không thể mã hóa
                data["access_token"] = token
                data["encrypted"] = False
                logging.warning("Failed to encrypt token, saving unencrypted")

            data["updated_at"] = datetime.now().isoformat()

            # Create backup of existing token file if it exists
            if os.path.exists(self.token_file):
                try:
                    backup_path = f"{self.token_file}.bak"
                    with open(self.token_file, "r") as src, open(
                        backup_path, "w"
                    ) as dst:
                        dst.write(src.read())
                    logging.debug(
                        f"Created backup of token file at {backup_path}"
                    )
                except Exception as e:
                    logging.warning(
                        f"Failed to create token file backup: {str(e)}"
                    )

            # Lưu vào file
            with open(self.token_file, "w") as f:
                json.dump(data, f, indent=2)

            logging.info(f"Token saved to {self.token_file}")
            return True
        except Exception as e:
            logging.error(f"Error saving token to file: {str(e)}")
            return False

    async def refresh_token_if_needed(self) -> Optional[str]:
        """Kiểm tra và làm mới token nếu cần"""
        current_token = await self.load_token()
        if not current_token:
            logging.warning("No token available to refresh")
            return None

        # Validate token
        validation = await self.auth_service.validate_token(current_token)

        # Nếu token hợp lệ thì trả về token hiện tại
        if validation.is_valid and (
            not validation.expires_at
            or (
                validation.expires_at and validation.expires_at > datetime.now()
            )
        ):
            return current_token

        # Nếu token không hợp lệ hoặc hết hạn, thử refresh
        new_token = await self.auth_service.refresh_token(current_token)
        if new_token:
            # Validate token mới
            new_validation = await self.auth_service.validate_token(new_token)

            # Lưu token mới
            await self.save_token(
                new_token,
                {
                    "expires_at": (
                        new_validation.expires_at.isoformat()
                        if new_validation.expires_at
                        else None
                    ),
                    "user_id": new_validation.user_id,
                    "scopes": new_validation.scopes,
                },
            )

            # Cập nhật settings runtime
            settings.FACEBOOK_ACCESS_TOKEN = new_token

            return new_token

        return None

    async def get_or_create_token(self) -> Optional[str]:
        """Lấy token hiện tại hoặc tạo mới nếu cần"""
        # Thử lấy token hiện tại
        token = await self.load_token()

        # Nếu có token, kiểm tra và làm mới nếu cần
        if token:
            return await self.refresh_token_if_needed()

        # Nếu không có token, cần flow OAuth mới
        logging.warning("No token available, need to complete OAuth flow")
        return None

    async def refresh_all_tokens(self) -> bool:
        """
        Làm mới tất cả các token đã lưu trữ

        Returns:
            bool: True nếu ít nhất một token được làm mới thành công, False nếu không
        """
        logging.info("Starting refresh of all stored tokens")
        success = False

        # Làm mới token chính (từ settings hoặc file)
        current_token = await self.load_token()
        if current_token:
            logging.info("Refreshing main access token")
            new_token = await self.refresh_token_if_needed()
            if new_token:
                success = True
                logging.info("Main token refreshed successfully")
            else:
                logging.warning("Failed to refresh main token")
        else:
            logging.warning("No main token found to refresh")

        # Làm mới tất cả token trong FacebookAuthService
        if not hasattr(self.auth_service, "tokens_data"):
            # Reload tokens từ file nếu cần
            self.auth_service._load_tokens()

        # Làm mới các user tokens
        if "user_tokens" in self.auth_service.tokens_data:
            for user_id, token_data in list(
                self.auth_service.tokens_data["user_tokens"].items()
            ):
                try:
                    # Lấy token từ storage
                    user_token = await self.auth_service._get_user_token(
                        user_id
                    )
                    if user_token and user_token.access_token:
                        # Làm mới token
                        new_token = await self.auth_service.refresh_token(
                            user_token.access_token
                        )
                        if new_token:
                            logging.info(f"Refreshed token for user {user_id}")
                            success = True
                except Exception as e:
                    logging.error(
                        f"Error refreshing token for user {user_id}: {str(e)}"
                    )

        return success

    async def refresh_expiring_tokens(
        self, hours_threshold: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Refresh tất cả tokens sắp hết hạn trong X giờ tới

        Args:
            hours_threshold: Số giờ trước khi token hết hạn

        Returns:
            Danh sách kết quả refresh cho mỗi token
        """
        logging.info(
            f"Starting refresh of tokens expiring in the next {hours_threshold} hours"
        )
        results = []
        refresh_count = 0
        error_count = 0

        # Đảm bảo tokens_data được tải
        if not hasattr(self.auth_service, "tokens_data"):
            self.auth_service._load_tokens()

        # Thời gian ngưỡng để refresh
        threshold_time = datetime.now() + timedelta(hours=hours_threshold)

        # Làm mới token chính (từ settings hoặc file)
        current_token = await self.load_token()
        if current_token:
            try:
                # Validate token để kiểm tra thời gian hết hạn
                validation = await self.auth_service.validate_token(
                    current_token
                )

                # Chỉ refresh nếu token sắp hết hạn trong khung thời gian
                if (
                    validation.expires_at
                    and validation.expires_at <= threshold_time
                ):
                    logging.info(
                        f"Main token expires at {validation.expires_at.isoformat()}, refreshing"
                    )

                    # Thử refresh với tối đa 3 lần retry
                    retry_count = 0
                    max_retries = 3
                    success = False

                    while retry_count < max_retries and not success:
                        try:
                            new_token = await self.auth_service.refresh_token(
                                current_token
                            )
                            if new_token:
                                new_validation = (
                                    await self.auth_service.validate_token(
                                        new_token
                                    )
                                )

                                # Lưu token mới
                                await self.save_token(
                                    new_token,
                                    {
                                        "expires_at": (
                                            new_validation.expires_at.isoformat()
                                            if new_validation.expires_at
                                            else None
                                        ),
                                        "user_id": new_validation.user_id,
                                        "scopes": new_validation.scopes,
                                    },
                                )

                                # Cập nhật settings runtime
                                settings.FACEBOOK_ACCESS_TOKEN = new_token

                                results.append(
                                    {
                                        "token_type": "main",
                                        "success": True,
                                        "message": "Token refreshed successfully",
                                        "expires_at": new_validation.expires_at,
                                        "retry_count": retry_count,
                                    }
                                )
                                refresh_count += 1
                                success = True
                            else:
                                retry_count += 1
                                if retry_count >= max_retries:
                                    results.append(
                                        {
                                            "token_type": "main",
                                            "success": False,
                                            "message": "Failed to refresh token after multiple attempts",
                                            "retry_count": retry_count,
                                        }
                                    )
                                    error_count += 1
                                logging.warning(
                                    f"Failed to refresh main token, attempt {retry_count}/{max_retries}"
                                )
                        except Exception as e:
                            retry_count += 1
                            logging.error(
                                f"Error refreshing main token (attempt {retry_count}/{max_retries}): {str(e)}"
                            )
                            if retry_count >= max_retries:
                                results.append(
                                    {
                                        "token_type": "main",
                                        "success": False,
                                        "message": f"Error refreshing token: {str(e)}",
                                        "retry_count": retry_count,
                                    }
                                )
                                error_count += 1
                else:
                    # Token chưa cần refresh
                    if validation.expires_at:
                        results.append(
                            {
                                "token_type": "main",
                                "success": True,
                                "message": "Token does not need refresh yet",
                                "expires_at": validation.expires_at,
                            }
                        )
                    else:
                        results.append(
                            {
                                "token_type": "main",
                                "success": True,
                                "message": "Token does not expire",
                                "expires_at": None,
                            }
                        )
            except Exception as e:
                logging.error(f"Error validating main token: {str(e)}")
                results.append(
                    {
                        "token_type": "main",
                        "success": False,
                        "message": f"Error validating token: {str(e)}",
                    }
                )
                error_count += 1

        # Làm mới các user tokens
        if "user_tokens" in self.auth_service.tokens_data:
            for user_id, token_data in list(
                self.auth_service.tokens_data["user_tokens"].items()
            ):
                try:
                    # Lấy token từ storage
                    user_token = await self.auth_service._get_user_token(
                        user_id
                    )
                    if not user_token or not user_token.access_token:
                        continue

                    # Kiểm tra xem token có sắp hết hạn không
                    if (
                        user_token.expires_at
                        and user_token.expires_at <= threshold_time
                    ):
                        logging.info(
                            f"Token for user {user_id} expires at {user_token.expires_at.isoformat()}, refreshing"
                        )

                        # Thực hiện refresh với retry
                        retry_count = 0
                        max_retries = 3
                        success = False

                        while retry_count < max_retries and not success:
                            try:
                                new_token = (
                                    await self.auth_service.refresh_token(
                                        user_token.access_token
                                    )
                                )
                                if new_token:
                                    # Validate thành công
                                    results.append(
                                        {
                                            "token_type": "user",
                                            "user_id": user_id,
                                            "success": True,
                                            "message": "User token refreshed successfully",
                                            "expires_at": user_token.expires_at,
                                            "retry_count": retry_count,
                                        }
                                    )
                                    refresh_count += 1
                                    success = True
                                else:
                                    retry_count += 1
                                    if retry_count >= max_retries:
                                        results.append(
                                            {
                                                "token_type": "user",
                                                "user_id": user_id,
                                                "success": False,
                                                "message": "Failed to refresh user token after multiple attempts",
                                                "retry_count": retry_count,
                                            }
                                        )
                                        error_count += 1
                            except Exception as e:
                                retry_count += 1
                                logging.error(
                                    f"Error refreshing token for user {user_id} (attempt {retry_count}/{max_retries}): {str(e)}"
                                )
                                if retry_count >= max_retries:
                                    results.append(
                                        {
                                            "token_type": "user",
                                            "user_id": user_id,
                                            "success": False,
                                            "message": f"Error refreshing token: {str(e)}",
                                            "retry_count": retry_count,
                                        }
                                    )
                                    error_count += 1
                    else:
                        # Token chưa cần refresh
                        if user_token.expires_at:
                            results.append(
                                {
                                    "token_type": "user",
                                    "user_id": user_id,
                                    "success": True,
                                    "message": "User token does not need refresh yet",
                                    "expires_at": user_token.expires_at,
                                }
                            )
                except Exception as e:
                    logging.error(
                        f"Error processing token for user {user_id}: {str(e)}"
                    )
                    results.append(
                        {
                            "token_type": "user",
                            "user_id": user_id,
                            "success": False,
                            "message": f"Error processing token: {str(e)}",
                        }
                    )
                    error_count += 1

        # Làm mới các page tokens (nếu cần)
        # Lưu ý: Page tokens thường không có thời hạn nên có thể không cần

        logging.info(
            f"Token refresh completed: {refresh_count} refreshed, {error_count} errors"
        )
        return results

    async def get_business_token(self, business_id: str) -> Optional[str]:
        """
        Lấy token cho Business từ kho lưu trữ

        Args:
            business_id: ID của Facebook Business

        Returns:
            Chuỗi token hoặc None nếu không tìm thấy
        """
        logging.info(f"Getting business token for business_id: {business_id}")

        try:
            # Kiểm tra xem dữ liệu token đã được tải chưa
            if not hasattr(self.auth_service, "tokens_data"):
                self.auth_service._load_tokens()

            # Kiểm tra xem có section business_tokens trong dữ liệu chưa
            if "business_tokens" not in self.auth_service.tokens_data:
                self.auth_service.tokens_data["business_tokens"] = {}

            # Kiểm tra xem có token cho business này không
            if business_id in self.auth_service.tokens_data["business_tokens"]:
                business_token_data = self.auth_service.tokens_data[
                    "business_tokens"
                ][business_id]

                # Lấy token từ dữ liệu
                token = business_token_data.get("access_token")

                # Kiểm tra xem token đã mã hóa chưa
                if token and business_token_data.get("encrypted", False):
                    # Giải mã token
                    token = TokenEncryption.decrypt_token(token)

                return token

            logging.warning(
                f"No business token found for business_id: {business_id}"
            )
            return None

        except Exception as e:
            logging.error(f"Error getting business token: {str(e)}")
            return None

    async def save_business_token(
        self, business_id: str, token: str, token_data: Dict = None
    ) -> bool:
        """
        Lưu Business token vào kho lưu trữ

        Args:
            business_id: ID của Facebook Business
            token: Token string cần lưu
            token_data: Thông tin bổ sung về token (scopes, expires_at, etc.)

        Returns:
            True nếu lưu thành công, False nếu có lỗi
        """
        logging.info(f"Saving business token for business_id: {business_id}")

        try:
            # Kiểm tra xem dữ liệu token đã được tải chưa
            if not hasattr(self.auth_service, "tokens_data"):
                self.auth_service._load_tokens()

            # Kiểm tra xem có section business_tokens trong dữ liệu chưa
            if "business_tokens" not in self.auth_service.tokens_data:
                self.auth_service.tokens_data["business_tokens"] = {}

            # Chuẩn bị dữ liệu token
            data = token_data or {}

            # Mã hóa token trước khi lưu, sử dụng encrypt_if_needed để tránh mã hóa lại
            encrypted_token, is_encrypted = TokenEncryption.encrypt_if_needed(
                token
            )
            if encrypted_token:
                data["access_token"] = encrypted_token
                data["encrypted"] = is_encrypted
                if is_encrypted:
                    logging.info(
                        f"Business token encrypted successfully for business_id: {business_id}"
                    )
                else:
                    logging.warning(
                        f"Failed to encrypt business token for business_id: {business_id}"
                    )
            else:
                # Fallback khi không thể mã hóa
                data["access_token"] = token
                data["encrypted"] = False
                logging.warning(
                    f"Failed to encrypt business token for business_id: {business_id}"
                )

            # Thêm thông tin timestamp
            data["updated_at"] = datetime.now().isoformat()

            # Lưu token vào dữ liệu
            self.auth_service.tokens_data["business_tokens"][business_id] = data

            # Lưu dữ liệu vào file
            if self.auth_service._save_tokens():
                logging.info(
                    f"Business token saved for business_id: {business_id}"
                )
                return True
            else:
                logging.error(
                    f"Failed to save business token for business_id: {business_id}"
                )
                return False

        except Exception as e:
            logging.error(f"Error saving business token: {str(e)}")
            return False

    async def check_token_permissions(
        self, token: str, required_permissions: List[str]
    ) -> TokenPermissionCheckResponse:
        """
        Kiểm tra xem token có đủ quyền không

        Args:
            token: Token cần kiểm tra quyền
            required_permissions: Danh sách các quyền cần thiết

        Returns:
            TokenPermissionCheckResponse object chứa kết quả kiểm tra
        """
        logging.info(
            f"Checking token permissions for {len(required_permissions)} required permissions"
        )

        if not token:
            return TokenPermissionCheckResponse.create_invalid(
                "No token provided"
            )

        try:
            # Validate token
            validation = await self.auth_service.validate_token(token)

            # Kiểm tra token có valid không
            if not validation.is_valid:
                return TokenPermissionCheckResponse.create_invalid(
                    validation.error_message or "Invalid token"
                )

            # Kiểm tra token có hết hạn không
            if validation.expires_at and validation.expires_at < datetime.now():
                # Tạo URL xác thực mới
                auth_url = self.auth_service.get_authorization_url(
                    scopes=required_permissions
                ).get("authorization_url")

                return TokenPermissionCheckResponse.create_expired(auth_url)

            # Lấy các quyền của token
            token_scopes = validation.scopes

            # Kiểm tra xem token có đủ tất cả các quyền cần thiết không
            missing_permissions = [
                perm
                for perm in required_permissions
                if perm not in token_scopes
            ]

            if not missing_permissions:
                # Token có đủ tất cả các quyền
                return TokenPermissionCheckResponse.create_success()
            else:
                # Token thiếu một số quyền, tạo URL xác thực mới với các quyền cần thiết
                auth_url = self.auth_service.get_authorization_url(
                    scopes=required_permissions
                ).get("authorization_url")

                return TokenPermissionCheckResponse.create_missing_permissions(
                    missing_permissions, auth_url
                )

        except FacebookRequestError as e:
            logging.error(
                f"Facebook API error during permission check: {str(e)}"
            )
            return TokenPermissionCheckResponse.create_invalid(
                f"Facebook API error: {e.api_error_message()}"
            )

        except Exception as e:
            logging.error(f"Error checking token permissions: {str(e)}")
            return TokenPermissionCheckResponse.create_invalid(
                f"Error checking permissions: {str(e)}"
            )

    async def refresh_token_on_demand(self, token: str) -> Optional[str]:
        """
        Làm mới token theo yêu cầu khi cần thiết

        Args:
            token: Token cần làm mới

        Returns:
            Token mới nếu làm mới thành công, None nếu thất bại
        """
        logging.info("Attempting to refresh token on demand")

        if not token:
            logging.warning("No token provided for refresh")
            return None

        try:
            # Validate token để kiểm tra trạng thái
            validation = await self.auth_service.validate_token(token)

            # Nếu token không hợp lệ, không thể làm mới
            if not validation.is_valid:
                logging.warning(
                    f"Cannot refresh invalid token: {validation.error_message}"
                )
                return None

            # Nếu token vẫn còn hạn và hợp lệ, không cần làm mới
            if not validation.expires_at or (
                validation.expires_at
                and validation.expires_at > datetime.now() + timedelta(days=1)
            ):
                logging.info(
                    "Token is still valid and not expiring soon, no refresh needed"
                )
                return token

            # Thử làm mới token
            logging.info(
                "Token is expiring soon or invalid, attempting to refresh"
            )
            new_token = await self.auth_service.refresh_token(token)

            if new_token:
                logging.info("Token refreshed successfully")

                # Lấy thông tin token mới
                new_validation = await self.auth_service.validate_token(
                    new_token
                )

                # Xác định loại token và lưu phù hợp
                if validation.user_id:
                    # Đây là user token
                    await self._store_refreshed_user_token(
                        validation.user_id, new_token, new_validation
                    )

                return new_token
            else:
                logging.warning("Failed to refresh token")
                return None

        except Exception as e:
            logging.error(f"Error refreshing token on demand: {str(e)}")
            return None

    async def _store_refreshed_user_token(
        self, user_id: str, token: str, validation: TokenValidationResponse
    ) -> None:
        """
        Lưu user token đã làm mới

        Args:
            user_id: ID của user
            token: Token mới
            validation: Kết quả validation của token mới
        """
        try:
            # Chuẩn bị token model
            user_token = FacebookUserToken(
                user_id=user_id,
                access_token=token,
                expires_at=validation.expires_at,
                is_valid=True,
                scopes=validation.scopes,
            )

            # Lưu vào storage
            await self.auth_service._store_user_token(user_token)
            logging.info(f"Refreshed token stored for user {user_id}")

        except Exception as e:
            logging.error(f"Error storing refreshed user token: {str(e)}")
