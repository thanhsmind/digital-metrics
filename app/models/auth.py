from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FacebookAuthCredential(BaseModel):
    """Thông tin xác thực cho Facebook OAuth"""

    app_id: str
    app_secret: str
    redirect_uri: str
    scopes: List[str]


class FacebookUserToken(BaseModel):
    """Model lưu trữ token của Facebook user"""

    user_id: str
    access_token: str
    token_type: str = "user"
    expires_at: Optional[datetime] = None
    is_valid: bool = True
    scopes: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class FacebookPageToken(BaseModel):
    """Model lưu trữ token của Facebook page"""

    user_id: str
    page_id: str
    page_name: str
    access_token: str
    token_type: str = "page"
    category: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class FacebookBusinessToken(BaseModel):
    """Model đại diện cho Business Access Token"""

    business_id: str
    access_token: str
    token_type: str = "business"
    app_id: str
    expires_at: Optional[datetime] = None
    is_valid: bool = True
    scopes: List[str] = []
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "business_id": "123456789",
                "access_token": "EAA...",
                "token_type": "business",
                "app_id": "987654321",
                "expires_at": "2023-12-31T23:59:59",
                "is_valid": True,
                "scopes": ["business_management", "ads_management"],
                "updated_at": "2023-01-01T12:00:00Z",
            }
        }


class TokenValidationResponse(BaseModel):
    """Kết quả của việc validate token"""

    is_valid: bool
    app_id: str
    application: str
    user_id: Optional[str] = None
    scopes: List[str] = []
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None


class TokenPermissionCheckResponse(BaseModel):
    """Model phản hồi sau khi kiểm tra quyền của token"""

    has_permission: bool
    missing_permissions: List[str] = []
    token_status: str = "valid"  # valid, expired, invalid
    authorization_url: Optional[str] = None
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "has_permission": False,
                "missing_permissions": [
                    "ads_management",
                    "business_management",
                ],
                "token_status": "valid",
                "authorization_url": "https://www.facebook.com/v17.0/dialog/oauth?...",
                "message": "Token lacks required permissions",
            }
        }

    @classmethod
    def create_success(
        cls, message: str = "Token has all required permissions"
    ):
        """Create a success response"""
        return cls(
            has_permission=True,
            missing_permissions=[],
            token_status="valid",
            message=message,
        )

    @classmethod
    def create_missing_permissions(
        cls, missing: List[str], auth_url: Optional[str] = None
    ):
        """Create a response for missing permissions"""
        return cls(
            has_permission=False,
            missing_permissions=missing,
            token_status="valid",
            authorization_url=auth_url,
            message=f"Token is missing required permissions: {', '.join(missing)}",
        )

    @classmethod
    def create_invalid(cls, reason: str = "Token is invalid"):
        """Create a response for invalid token"""
        return cls(has_permission=False, token_status="invalid", message=reason)

    @classmethod
    def create_expired(cls, auth_url: Optional[str] = None):
        """Create a response for expired token"""
        return cls(
            has_permission=False,
            token_status="expired",
            authorization_url=auth_url,
            message="Token has expired",
        )


class TokenRefreshResponse(BaseModel):
    """Kết quả của việc refresh token"""

    success: bool
    message: str
    new_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_valid: Optional[bool] = None


class AuthError(Exception):
    """Exception cho các lỗi xác thực"""

    def __init__(self, message: str, error_code: str = "auth_error"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)
