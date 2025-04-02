import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Digital Metrics API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG_MODE: bool = True

    # Secret key cho mã hóa
    SECRET_KEY: str = "token_encryption_key_change_in_production"

    # API Key cho internal endpoints
    INTERNAL_API_KEY: str = "internal_api_key_change_in_production"

    # Facebook configuration
    FACEBOOK_APP_ID: Optional[str] = None
    FACEBOOK_APP_SECRET: Optional[str] = None
    FACEBOOK_ACCESS_TOKEN: Optional[str] = None
    FACEBOOK_API_VERSION: str = "v18.0"
    FACEBOOK_REDIRECT_URI: str = (
        "http://localhost:8000/api/v1/auth/facebook/callback"
    )

    # Google configuration
    GOOGLE_ADS_CONFIG_FILE: str = "config/google-ads.yaml"

    # File paths for token storage
    TOKEN_STORAGE_DIR: str = "tokens"
    FACEBOOK_TOKEN_FILE: str = "tokens/facebook_tokens.json"
    GOOGLE_TOKEN_FILE: str = "tokens/google_tokens.json"

    # Cấu hình cho file config chung
    CONFIG_FILE: str = "config/config.json"

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "allow",
    }


settings = Settings()
