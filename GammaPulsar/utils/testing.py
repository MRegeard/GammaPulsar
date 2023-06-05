from functools import wraps
from loguru import logger as log

__all__ = ["disable_logging_library"]


def disable_logging_library(name):
    @wraps(name)
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            log.disable(name)
            try:
                result = func(*args, **kwargs)
            finally:
                log.enable(name)
            return result

        return wrapper

    return decorator
