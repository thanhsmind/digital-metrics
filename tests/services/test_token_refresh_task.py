import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tasks.token_refresh import TokenRefreshTask


@pytest.fixture
def mock_token_manager():
    """Fixture để mock TokenManager"""
    mock = AsyncMock()
    mock.refresh_token_if_needed = AsyncMock()
    mock.refresh_expiring_tokens = AsyncMock()
    return mock


@pytest.fixture
def mock_api_manager():
    """Fixture để mock FacebookApiManager"""
    mock = MagicMock()
    mock.update_access_token = MagicMock()
    return mock


@pytest.fixture
def token_refresh_task(mock_token_manager, mock_api_manager):
    """Fixture để tạo TokenRefreshTask với mocked dependencies"""
    with patch(
        "app.tasks.token_refresh.TokenManager", return_value=mock_token_manager
    ):
        with patch(
            "app.tasks.token_refresh.FacebookApiManager",
            return_value=mock_api_manager,
        ):
            task = TokenRefreshTask()
            # Patch task.refresh_task để tránh việc tạo task thật trên event loop
            task.refresh_task = None
            return task


@pytest.mark.asyncio
async def test_start_background_task(token_refresh_task):
    """Test start_background_task"""
    # Tạo mock BackgroundTasks
    mock_background_tasks = MagicMock()
    mock_background_tasks.add_task = MagicMock()

    # Gọi method cần test
    await token_refresh_task.start_background_task(mock_background_tasks)

    # Verify mock được gọi
    mock_background_tasks.add_task.assert_called_once()
    assert (
        token_refresh_task.is_running is False
    )  # Chỉ set là True khi task chạy


@pytest.mark.asyncio
async def test_refresh_token_now(
    token_refresh_task, mock_token_manager, mock_api_manager
):
    """Test refresh_token_now với token mới"""
    # Setup mock trả về token mới
    mock_token_manager.refresh_token_if_needed.return_value = "new_token"

    # Gọi method cần test
    result = await token_refresh_task.refresh_token_now()

    # Verify kết quả
    assert result is True
    mock_token_manager.refresh_token_if_needed.assert_called_once()
    mock_api_manager.update_access_token.assert_called_once_with("new_token")


@pytest.mark.asyncio
async def test_refresh_token_now_no_token(
    token_refresh_task, mock_token_manager, mock_api_manager
):
    """Test refresh_token_now khi không có token mới"""
    # Setup mock không có token mới
    mock_token_manager.refresh_token_if_needed.return_value = None

    # Gọi method cần test
    result = await token_refresh_task.refresh_token_now()

    # Verify kết quả
    assert result is False
    mock_token_manager.refresh_token_if_needed.assert_called_once()
    mock_api_manager.update_access_token.assert_not_called()


@pytest.mark.asyncio
async def test_refresh_token_now_with_error(
    token_refresh_task, mock_token_manager
):
    """Test refresh_token_now khi có lỗi"""
    # Setup mock throw exception
    mock_token_manager.refresh_token_if_needed.side_effect = Exception(
        "Test error"
    )

    # Gọi method cần test
    result = await token_refresh_task.refresh_token_now()

    # Verify kết quả
    assert result is False
    mock_token_manager.refresh_token_if_needed.assert_called_once()


@pytest.mark.asyncio
async def test_schedule_periodic_refresh(token_refresh_task):
    """Test schedule_periodic_refresh"""
    # Patch asyncio.create_task để tránh tạo task thật
    with patch("asyncio.create_task") as mock_create_task:
        mock_task = MagicMock()
        mock_task.done.return_value = False
        mock_create_task.return_value = mock_task

        # Giả lập task đang chạy
        token_refresh_task.refresh_task = mock_task

        # Gọi method cần test
        result = await token_refresh_task.schedule_periodic_refresh(hours=12)

        # Verify kết quả
        assert result is True
        assert token_refresh_task.refresh_interval_hours == 12
        mock_task.cancel.assert_called_once()  # Task cũ bị cancel
        mock_create_task.assert_called_once()  # Task mới được tạo


@pytest.mark.asyncio
async def test_run_scheduled_refresh(token_refresh_task, mock_token_manager):
    """Test run_scheduled_refresh"""
    # Setup mock cho token_manager.refresh_expiring_tokens
    mock_token_manager.refresh_expiring_tokens.return_value = [
        {"success": True, "message": "Token refreshed"},
        {"success": True, "message": "Token still valid"},
        {"success": False, "message": "Error refreshing"},
    ]

    # Patch asyncio.sleep để tránh đợi thật
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        # Patch để đảm bảo loop chỉ chạy một lần
        mock_sleep.side_effect = asyncio.CancelledError()

        # Gọi method cần test và bắt exception để handle loop exit
        with pytest.raises(asyncio.CancelledError):
            await token_refresh_task.run_scheduled_refresh(hours=12)

        # Verify các calls
        mock_token_manager.refresh_expiring_tokens.assert_called_once_with(24)
        mock_sleep.assert_called_once()
