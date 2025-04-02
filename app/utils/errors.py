"""Error handling utilities cho Digital Metrics API."""

from typing import Any, Dict, List, Optional, Type, Union

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Custom exception classes


class APIError(Exception):
    """
    Base class cho tất cả API errors.

    Attributes:
        message: Thông báo lỗi
        status_code: HTTP status code
        error_code: Mã lỗi dùng cho client
        details: Thông tin chi tiết về lỗi
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)


class ValidationError(APIError):
    """
    Error khi validation fails.

    Attributes:
        message: Thông báo lỗi
        details: Thông tin chi tiết về validation errors
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class ConfigError(APIError):
    """
    Error khi configuration loading hoặc validation fails.

    Attributes:
        message: Thông báo lỗi
    """

    def __init__(self, message: str):
        super().__init__(
            message=message, status_code=500, error_code="CONFIG_ERROR"
        )


class AuthenticationError(APIError):
    """
    Error khi authentication fails.

    Attributes:
        message: Thông báo lỗi
    """

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message, status_code=401, error_code="AUTHENTICATION_ERROR"
        )


class NotFoundError(APIError):
    """
    Error khi resource không tồn tại.

    Attributes:
        resource: Tên của resource
        resource_id: ID của resource (nếu có)
    """

    def __init__(self, resource: str, resource_id: Optional[str] = None):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with ID {resource_id} not found"

        super().__init__(
            message=message, status_code=404, error_code="NOT_FOUND_ERROR"
        )


# Error serialization


def serialize_error(error: Union[APIError, Exception]) -> Dict[str, Any]:
    """
    Serialize error thành JSON response.

    Args:
        error: Exception object

    Returns:
        Dictionary chứa thông tin lỗi đã được serialize

    Examples:
        >>> err = ValidationError("Invalid data", {"field": "This field is required"})
        >>> result = serialize_error(err)
        >>> result["success"]
        False
        >>> result["message"]
        'Invalid data'
        >>> result["error_code"]
        'VALIDATION_ERROR'
    """
    if isinstance(error, APIError):
        error_response = {
            "success": False,
            "message": error.message,
            "error_code": error.error_code,
        }
        if error.details:
            error_response["details"] = error.details
        return error_response

    # Generic error
    return {
        "success": False,
        "message": str(error),
        "error_code": "INTERNAL_SERVER_ERROR",
    }


# Exception handlers


def add_exception_handlers(app: FastAPI) -> None:
    """
    Add tất cả exception handlers to FastAPI app.

    Args:
        app: FastAPI instance

    Examples:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> add_exception_handlers(app)
    """

    @app.exception_handler(APIError)
    async def handle_api_error(request: Request, error: APIError):
        return JSONResponse(
            status_code=error.status_code, content=serialize_error(error)
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, error: RequestValidationError
    ):
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": "Invalid request parameters",
                "error_code": "VALIDATION_ERROR",
                "details": error.errors(),
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request, error: StarletteHTTPException
    ):
        return JSONResponse(
            status_code=error.status_code,
            content={
                "success": False,
                "message": error.detail,
                "error_code": f"HTTP_ERROR_{error.status_code}",
            },
        )

    @app.exception_handler(Exception)
    async def handle_generic_exception(request: Request, error: Exception):
        return JSONResponse(status_code=500, content=serialize_error(error))
