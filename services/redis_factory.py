from redis import Redis

from config.redis_config import RedisConfig


def create_redis_client(config: RedisConfig) -> Redis:
    """
    Tạo Redis client instance từ config.

    Args:
        config: RedisConfig instance chứa thông tin cấu hình Redis

    Returns:
        Redis client instance đã được cấu hình

    Raises:
        ConnectionError: Khi không thể kết nối tới Redis server
    """
    return Redis(
        host=config.host,
        port=config.port,
        db=config.db,
        password=config.password,
        ssl=config.ssl,
        encoding=config.encoding,
        socket_timeout=config.socket_timeout,
        retry_on_timeout=config.retry_on_timeout,
        max_connections=config.max_connections,
        decode_responses=True,
    )
