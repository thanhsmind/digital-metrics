import json
import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from freezegun import freeze_time

from app.models.auth import FacebookUserToken, TokenValidationResponse
from app.services.facebook.auth_service import FacebookAuthService
from app.services.facebook.token_manager import TokenManager


@pytest.fixture
def mock_auth_service():
    """Fixture để mock FacebookAuthService"""
    with patch(
        "app.services.facebook.token_manager.FacebookAuthService"
    ) as mock:
        service = mock.return_value
        service.app_id = "mock_app_id"
        service.app_secret = "mock_app_secret"
        service.api_version = "v18.0"

        # Setup các phương thức async
        service.validate_token = AsyncMock()
        service.refresh_token = AsyncMock()
        service._get_user_token = AsyncMock()
        service._store_user_token = AsyncMock()

        # Setup tokens_data
        service.tokens_data = {
            "user_tokens": {
                "user1": {"access_token": "mock_token1", "encrypted": False},
                "user2": {"access_token": "mock_token2", "encrypted": False},
            }
        }
        service._load_tokens = MagicMock()

        yield service


@pytest.fixture
def token_manager(mock_auth_service, tmp_path):
    """Fixture để tạo TokenManager với mock dependencies"""
    manager = TokenManager()
    manager.auth_service = mock_auth_service
    manager.token_file = os.path.join(tmp_path, "test_tokens.json")
    manager.load_token = AsyncMock()
    manager.save_token = AsyncMock(return_value=True)
    return manager


@pytest.mark.asyncio
async def test_refresh_expiring_tokens_with_expiring_token(
    token_manager, mock_auth_service
):
    """Test refresh tokens với token sắp hết hạn"""
    # Thiết lập mock cho token chính
    expiry_time = datetime.now() + timedelta(
        hours=5
    )  # Token hết hạn trong 5 giờ
    token_manager.load_token.return_value = "main_test_token"

    # Mock validate_token để trả về token sắp hết hạn
    main_validation = TokenValidationResponse(
        is_valid=True,
        app_id="mock_app_id",
        application="Mock App",
        user_id="main_user",
        expires_at=expiry_time,
        scopes=["email", "pages_read_engagement"],
    )
    mock_auth_service.validate_token.return_value = main_validation

    # Mock refresh_token để trả về token mới
    mock_auth_service.refresh_token.return_value = "new_test_token"

    # Thực hiện refresh
    with freeze_time("2023-01-15 12:00:00"):
        results = await token_manager.refresh_expiring_tokens(
            hours_threshold=24
        )

    # Kiểm tra kết quả
    assert len(results) >= 1
    main_result = [r for r in results if r.get("token_type") == "main"][0]
    assert main_result["success"] is True
    assert "Token refreshed" in main_result["message"]

    # Verify các mock calls
    token_manager.load_token.assert_called_once()
    mock_auth_service.validate_token.assert_called_with("main_test_token")
    mock_auth_service.refresh_token.assert_called_with("main_test_token")
    token_manager.save_token.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_expiring_tokens_with_valid_token(
    token_manager, mock_auth_service
):
    """Test refresh tokens với token còn hạn dài"""
    # Thiết lập mock cho token chính
    expiry_time = datetime.now() + timedelta(days=30)  # Token còn hạn dài
    token_manager.load_token.return_value = "main_test_token"

    # Mock validate_token để trả về token còn hạn dài
    main_validation = TokenValidationResponse(
        is_valid=True,
        app_id="mock_app_id",
        application="Mock App",
        user_id="main_user",
        expires_at=expiry_time,
        scopes=["email", "pages_read_engagement"],
    )
    mock_auth_service.validate_token.return_value = main_validation

    # Thực hiện refresh
    with freeze_time("2023-01-15 12:00:00"):
        results = await token_manager.refresh_expiring_tokens(
            hours_threshold=24
        )

    # Kiểm tra kết quả
    assert len(results) >= 1
    main_result = [r for r in results if r.get("token_type") == "main"][0]
    assert main_result["success"] is True
    assert "does not need refresh" in main_result["message"]

    # Verify rằng refresh_token không được gọi
    mock_auth_service.refresh_token.assert_not_called()


@pytest.mark.asyncio
async def test_refresh_expiring_tokens_with_user_tokens(
    token_manager, mock_auth_service
):
    """Test refresh user tokens"""
    # Thiết lập mock cho token chính (không quan trọng trong test này)
    token_manager.load_token.return_value = None

    # Mock _get_user_token cho hai users
    expiring_user = FacebookUserToken(
        user_id="user1",
        access_token="user1_token",
        expires_at=datetime.now() + timedelta(hours=5),
    )
    valid_user = FacebookUserToken(
        user_id="user2",
        access_token="user2_token",
        expires_at=datetime.now() + timedelta(days=30),
    )

    # Mock để trả về token cho từng user
    async def get_user_token_side_effect(user_id):
        if user_id == "user1":
            return expiring_user
        elif user_id == "user2":
            return valid_user
        return None

    mock_auth_service._get_user_token.side_effect = get_user_token_side_effect

    # Mock refresh_token cho user1
    mock_auth_service.refresh_token.return_value = "new_user1_token"

    # Thực hiện refresh
    with freeze_time("2023-01-15 12:00:00"):
        results = await token_manager.refresh_expiring_tokens(
            hours_threshold=24
        )

    # Kiểm tra kết quả
    user_results = [r for r in results if r.get("token_type") == "user"]
    assert len(user_results) == 2

    # Kiểm tra user1 (token sắp hết hạn)
    user1_result = [r for r in user_results if r.get("user_id") == "user1"][0]
    assert user1_result["success"] is True
    assert "refreshed successfully" in user1_result["message"]

    # Kiểm tra user2 (token còn hạn)
    user2_result = [r for r in user_results if r.get("user_id") == "user2"][0]
    assert user2_result["success"] is True
    assert "does not need refresh" in user2_result["message"]

    # Verify calls
    assert mock_auth_service._get_user_token.call_count == 2
    mock_auth_service.refresh_token.assert_called_once_with("user1_token")


@pytest.mark.asyncio
async def test_refresh_expiring_tokens_with_errors(
    token_manager, mock_auth_service
):
    """Test refresh tokens với lỗi"""
    # Thiết lập mock cho token chính
    token_manager.load_token.return_value = "main_test_token"

    # Mock validate_token để trả về token sắp hết hạn
    expiry_time = datetime.now() + timedelta(hours=5)
    main_validation = TokenValidationResponse(
        is_valid=True,
        app_id="mock_app_id",
        application="Mock App",
        user_id="main_user",
        expires_at=expiry_time,
        scopes=["email", "pages_read_engagement"],
    )
    mock_auth_service.validate_token.return_value = main_validation

    # Mock refresh_token để throw exception
    mock_auth_service.refresh_token.side_effect = Exception(
        "Mock refresh error"
    )

    # Thực hiện refresh
    with freeze_time("2023-01-15 12:00:00"):
        results = await token_manager.refresh_expiring_tokens(
            hours_threshold=24
        )

    # Kiểm tra kết quả
    assert len(results) >= 1
    main_result = [r for r in results if r.get("token_type") == "main"][0]
    assert main_result["success"] is False
    assert "Error refreshing token" in main_result["message"]
    assert main_result.get("retry_count") == 3  # Max retries đạt được
