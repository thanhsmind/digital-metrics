import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Digital Metrics API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG_MODE: bool = True

    # Redis configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: str = "6379"
    REDIS_PASSWORD: str = "secure_password"
    REDIS_SSL: str = "false"
    REDIS_DB: str = "0"
    REDIS_MAX_CONNECTIONS: str = "100"

    # Facebook configuration
    FACEBOOK_APP_ID: Optional[str] = None
    FACEBOOK_APP_SECRET: Optional[str] = None
    FACEBOOK_ACCESS_TOKEN: Optional[str] = None
    FACEBOOK_API_VERSION: str = "v18.0"
    FACEBOOK_REDIRECT_URI: str = (
        "http://localhost:8000/api/v1/auth/facebook/callback"
    )

    # File paths
    CONFIG_FILE: str = "config.json"
    GOOGLE_ADS_CONFIG_FILE: str = "config/google-ads.yaml"

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "allow",
    }


settings = Settings()
