from functools import wraps


class DatabaseError(Exception):
    """数据库操作异常"""

    pass


def db_catch(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            operation = func.__name__
            raise DatabaseError(f"Database  {operation} failed: {e}")

    return wrapper
