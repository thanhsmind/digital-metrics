from typing import Optional

from pydantic import BaseModel


class RedisConfig(BaseModel):
    """Redis configuration model."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    encoding: str = "utf-8"
    socket_timeout: int = 5
    retry_on_timeout: bool = True
    max_connections: int = 100
