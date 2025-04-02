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


class TokenValidationResponse(BaseModel):
    """Kết quả của việc validate token"""

    is_valid: bool
    app_id: str
    application: str
    user_id: Optional[str] = None
    scopes: List[str] = []
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None


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
