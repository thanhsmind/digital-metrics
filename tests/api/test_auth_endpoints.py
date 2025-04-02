from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from freezegun import freeze_time

from app.api.v1.endpoints.auth import scheduled_refresh, token_manager
from app.core.config import settings


@pytest.fixture
def test_app():
    app = FastAPI()
    app.include_router(scheduled_refresh.router, prefix="/api/v1/auth")
    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


@pytest.fixture
def mock_token_manager():
    with patch("app.api.v1.endpoints.auth.token_manager") as mock:
        mock.refresh_expiring_tokens = AsyncMock()
        yield mock


@pytest.mark.asyncio
async def test_scheduled_refresh_success(mock_token_manager):
    """Test endpoint scheduled_refresh với refresh token thành công"""
    # Mock kết quả trả về từ token_manager.refresh_expiring_tokens
    mock_token_manager.refresh_expiring_tokens.return_value = [
        {
            "token_type": "main",
            "success": True,
            "message": "Token refreshed successfully",
        },
        {
            "token_type": "user",
            "user_id": "123",
            "success": True,
            "message": "User token refreshed successfully",
        },
    ]

    # Mock FacebookAuthService
    with patch("app.api.v1.endpoints.auth.facebook_auth_service") as mock_auth:
        mock_auth.app_id = "test_app_id"
        mock_auth.app_secret = "test_app_secret"

        # Mock api_key để bypass authentication
        api_key = settings.INTERNAL_API_KEY

        # Gọi endpoint trực tiếp
        with freeze_time("2023-01-15 12:00:00"):
            response = await scheduled_refresh(
                hours_threshold=12, api_key=api_key
            )

        # Verify kết quả
        assert response["success"] is True
        assert "Refreshed 2 tokens" in response["message"]
        assert response["total_tokens"] == 2
        assert response["success_count"] == 2
        assert response["error_count"] == 0
        assert len(response["results"]) == 2

        # Verify mock call
        mock_token_manager.refresh_expiring_tokens.assert_called_once_with(12)


@pytest.mark.asyncio
async def test_scheduled_refresh_partial_success(mock_token_manager):
    """Test endpoint scheduled_refresh với kết quả tốt và lỗi hỗn hợp"""
    # Mock kết quả trả về từ token_manager.refresh_expiring_tokens
    mock_token_manager.refresh_expiring_tokens.return_value = [
        {
            "token_type": "main",
            "success": True,
            "message": "Token refreshed successfully",
        },
        {
            "token_type": "user",
            "user_id": "123",
            "success": False,
            "message": "Error refreshing token",
        },
    ]

    # Mock FacebookAuthService
    with patch("app.api.v1.endpoints.auth.facebook_auth_service") as mock_auth:
        mock_auth.app_id = "test_app_id"
        mock_auth.app_secret = "test_app_secret"

        # Mock api_key để bypass authentication
        api_key = settings.INTERNAL_API_KEY

        # Gọi endpoint trực tiếp
        with freeze_time("2023-01-15 12:00:00"):
            response = await scheduled_refresh(
                hours_threshold=24, api_key=api_key
            )

        # Verify kết quả
        assert (
            response["success"] is True
        )  # Vẫn success vì có ít nhất 1 token được refresh
        assert "Refreshed 1 tokens, 1 errors" in response["message"]
        assert response["total_tokens"] == 2
        assert response["success_count"] == 1
        assert response["error_count"] == 1
        assert len(response["results"]) == 2

        # Verify mock call
        mock_token_manager.refresh_expiring_tokens.assert_called_once_with(24)


@pytest.mark.asyncio
async def test_scheduled_refresh_all_failed(mock_token_manager):
    """Test endpoint scheduled_refresh với tất cả tokens đều refresh thất bại"""
    # Mock kết quả trả về từ token_manager.refresh_expiring_tokens
    mock_token_manager.refresh_expiring_tokens.return_value = [
        {
            "token_type": "main",
            "success": False,
            "message": "Error refreshing token",
        },
        {
            "token_type": "user",
            "user_id": "123",
            "success": False,
            "message": "Error refreshing token",
        },
    ]

    # Mock FacebookAuthService
    with patch("app.api.v1.endpoints.auth.facebook_auth_service") as mock_auth:
        mock_auth.app_id = "test_app_id"
        mock_auth.app_secret = "test_app_secret"

        # Mock api_key để bypass authentication
        api_key = settings.INTERNAL_API_KEY

        # Gọi endpoint trực tiếp
        with freeze_time("2023-01-15 12:00:00"):
            response = await scheduled_refresh(
                hours_threshold=24, api_key=api_key
            )

        # Verify kết quả
        assert response["success"] is False
        assert "Refreshed 0 tokens, 2 errors" in response["message"]
        assert response["total_tokens"] == 2
        assert response["success_count"] == 0
        assert response["error_count"] == 2
        assert len(response["results"]) == 2

        # Verify mock call
        mock_token_manager.refresh_expiring_tokens.assert_called_once_with(24)


@pytest.mark.asyncio
async def test_scheduled_refresh_no_tokens(mock_token_manager):
    """Test endpoint scheduled_refresh khi không có tokens cần refresh"""
    # Mock kết quả trả về từ token_manager.refresh_expiring_tokens
    mock_token_manager.refresh_expiring_tokens.return_value = []

    # Mock FacebookAuthService
    with patch("app.api.v1.endpoints.auth.facebook_auth_service") as mock_auth:
        mock_auth.app_id = "test_app_id"
        mock_auth.app_secret = "test_app_secret"

        # Mock api_key để bypass authentication
        api_key = settings.INTERNAL_API_KEY

        # Gọi endpoint trực tiếp
        with freeze_time("2023-01-15 12:00:00"):
            response = await scheduled_refresh(
                hours_threshold=24, api_key=api_key
            )

        # Verify kết quả
        assert response["success"] is False
        assert "Refreshed 0 tokens, 0 errors" in response["message"]
        assert response["total_tokens"] == 0
        assert response["success_count"] == 0
        assert response["error_count"] == 0
        assert len(response["results"]) == 0

        # Verify mock call
        mock_token_manager.refresh_expiring_tokens.assert_called_once_with(24)
