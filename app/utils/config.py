"""Configuration utilities cho Digital Metrics API."""

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field, field_validator

from app.utils.errors import ConfigError
from app.utils.logging import get_logger

logger = get_logger("config")


class DatabaseConfig(BaseModel):
    """Model cho database configuration."""

    host: str = Field(..., description="Database host address")
    port: int = Field(5432, description="Database port")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    database: str = Field(..., description="Database name")
    pool_size: int = Field(5, description="Connection pool size")
    ssl_mode: Optional[str] = Field(
        None, description="SSL mode for database connection"
    )

    def get_connection_string(self) -> str:
        """
        Build connection string từ config.

        Returns:
            SQLAlchemy connection string

        Examples:
            >>> config = DatabaseConfig(
            ...     host="localhost",
            ...     port=5432,
            ...     username="user",
            ...     password="pass",
            ...     database="metrics"
            ... )
            >>> config.get_connection_string()
            'postgresql://user:pass@localhost:5432/metrics'
        """
        conn_str = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

        if self.ssl_mode:
            conn_str += f"?sslmode={self.ssl_mode}"

        return conn_str


class APIConfig(BaseModel):
    """Model cho API configuration."""

    host: str = Field("0.0.0.0", description="API host address")
    port: int = Field(8000, description="API port")
    debug: bool = Field(False, description="Enable debug mode")
    cors_origins: List[str] = Field(["*"], description="CORS allowed origins")
    api_key_header: str = Field(
        "X-API-Key", description="Header name for API key"
    )
    log_level: str = Field("INFO", description="Log level")


class FacebookConfig(BaseModel):
    """Model cho Facebook API configuration."""

    app_id: str = Field(..., description="Facebook App ID")
    app_secret: str = Field(..., description="Facebook App Secret")
    api_version: str = Field("v17.0", description="Facebook API version")
    access_token: Optional[str] = Field(
        None, description="Facebook access token"
    )


class GoogleConfig(BaseModel):
    """Model cho Google Ads API configuration."""

    client_id: str = Field(..., description="Google client ID")
    client_secret: str = Field(..., description="Google client secret")
    developer_token: str = Field(..., description="Google developer token")
    refresh_token: Optional[str] = Field(
        None, description="Google refresh token"
    )


class AppConfig(BaseModel):
    """Main application configuration model."""

    env: str = Field(
        "development",
        description="Environment (development, staging, production)",
    )
    debug: bool = Field(False, description="Enable debug mode")
    api: APIConfig = Field(APIConfig(), description="API configuration")
    database: DatabaseConfig = Field(..., description="Database configuration")
    facebook: Optional[FacebookConfig] = Field(
        None, description="Facebook API configuration"
    )
    google: Optional[GoogleConfig] = Field(
        None, description="Google Ads API configuration"
    )
    log_to_file: bool = Field(
        False, description="Whether logs should be written to file"
    )
    log_file_path: Optional[str] = Field(None, description="Log file path")

    @field_validator("env")
    def validate_env(cls, v: str) -> str:
        """Validate environment setting."""
        allowed = ["development", "staging", "production", "testing"]
        if v not in allowed:
            raise ValueError(
                f"Environment must be one of: {', '.join(allowed)}"
            )
        return v


def load_config_from_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load configuration from YAML hoặc JSON file.

    Args:
        file_path: Path đến configuration file

    Returns:
        Dict với configuration

    Raises:
        ConfigError: Nếu có lỗi loading config

    Examples:
        >>> try:
        ...     config = load_config_from_file("config.yaml")
        ... except ConfigError as e:
        ...     print(f"Error: {str(e)}")
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise ConfigError(f"Config file not found: {file_path}")

    logger.info(f"Loading configuration from {file_path}")

    try:
        if file_path.suffix.lower() in [".yml", ".yaml"]:
            with open(file_path, "r") as f:
                return yaml.safe_load(f)
        elif file_path.suffix.lower() == ".json":
            with open(file_path, "r") as f:
                return json.load(f)
        else:
            raise ConfigError(
                f"Unsupported config file format: {file_path.suffix}"
            )
    except Exception as e:
        raise ConfigError(f"Failed to load config file: {str(e)}")


def load_config_from_env() -> Dict[str, Any]:
    """
    Load configuration từ environment variables.

    Returns:
        Dict với configuration

    Examples:
        >>> os.environ["DATABASE_HOST"] = "localhost"
        >>> os.environ["DATABASE_PORT"] = "5432"
        >>> config = load_config_from_env()
        >>> "database" in config
        True
    """
    logger.info("Loading configuration from environment variables")

    config = {
        "env": os.getenv("APP_ENV", "development"),
        "debug": os.getenv("APP_DEBUG", "false").lower() == "true",
        "api": {
            "host": os.getenv("API_HOST", "0.0.0.0"),
            "port": int(os.getenv("API_PORT", "8000")),
            "debug": os.getenv("API_DEBUG", "false").lower() == "true",
            "cors_origins": os.getenv("API_CORS_ORIGINS", "*").split(","),
            "api_key_header": os.getenv("API_KEY_HEADER", "X-API-Key"),
            "log_level": os.getenv("API_LOG_LEVEL", "INFO"),
        },
        "database": {
            "host": os.getenv("DATABASE_HOST", ""),
            "port": int(os.getenv("DATABASE_PORT", "5432")),
            "username": os.getenv("DATABASE_USERNAME", ""),
            "password": os.getenv("DATABASE_PASSWORD", ""),
            "database": os.getenv("DATABASE_NAME", ""),
            "pool_size": int(os.getenv("DATABASE_POOL_SIZE", "5")),
            "ssl_mode": os.getenv("DATABASE_SSL_MODE", None),
        },
        "log_to_file": os.getenv("LOG_TO_FILE", "false").lower() == "true",
        "log_file_path": os.getenv("LOG_FILE_PATH", None),
    }

    # Facebook config (optional)
    if os.getenv("FACEBOOK_APP_ID"):
        config["facebook"] = {
            "app_id": os.getenv("FACEBOOK_APP_ID", ""),
            "app_secret": os.getenv("FACEBOOK_APP_SECRET", ""),
            "api_version": os.getenv("FACEBOOK_API_VERSION", "v17.0"),
            "access_token": os.getenv("FACEBOOK_ACCESS_TOKEN", None),
        }

    # Google config (optional)
    if os.getenv("GOOGLE_CLIENT_ID"):
        config["google"] = {
            "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
            "developer_token": os.getenv("GOOGLE_DEVELOPER_TOKEN", ""),
            "refresh_token": os.getenv("GOOGLE_REFRESH_TOKEN", None),
        }

    return config


@lru_cache()
def load_app_config(
    config_file: Optional[Union[str, Path]] = None,
) -> AppConfig:
    """
    Load và validate application configuration.

    Args:
        config_file: Optional path đến configuration file

    Returns:
        AppConfig instance

    Raises:
        ConfigError: Nếu config invalid

    Examples:
        >>> try:
        ...     config = load_app_config()
        ...     print(f"Loaded config for environment: {config.env}")
        ... except ConfigError as e:
        ...     print(f"Configuration error: {str(e)}")
    """
    # Load từ file nếu specified
    if config_file:
        try:
            config_data = load_config_from_file(config_file)
        except ConfigError as e:
            logger.error(f"Failed to load config from file: {str(e)}")
            logger.info("Falling back to environment variables")
            config_data = load_config_from_env()
    else:
        # Load từ environment variables
        config_data = load_config_from_env()

    # Validate và tạo config object
    try:
        app_config = AppConfig(**config_data)
        logger.info(f"Loaded configuration for environment: {app_config.env}")
        return app_config
    except Exception as e:
        raise ConfigError(f"Invalid configuration: {str(e)}")


def get_config() -> AppConfig:
    """
    Get application configuration. Use file từ CONFIG_FILE env var nếu có,
    không thì dùng environment variables.

    Returns:
        AppConfig instance

    Examples:
        >>> config = get_config()
        >>> config.env
        'development'
    """
    config_file = os.getenv("CONFIG_FILE")
    return load_app_config(config_file)
