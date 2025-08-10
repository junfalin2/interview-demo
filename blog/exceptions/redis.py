from functools import wraps
import redis


class CacheError(Exception):
    """缓存操作异常"""

    pass


def redis_catch(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except redis.RedisError as e:
            operation = func.__name__
            raise CacheError(f"Redis {operation} failed: {e}")

    return wrapper
