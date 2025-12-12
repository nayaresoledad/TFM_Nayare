import time
import functools
from typing import Callable, Tuple, Type


def retry(max_attempts: int = 3, initial_delay: float = 1.0, backoff: float = 2.0, exceptions: Tuple[Type[BaseException], ...] = (Exception,)):
    """Simple retry decorator with exponential backoff.

    Args:
        max_attempts: number of attempts (including first).
        initial_delay: delay before first retry in seconds.
        backoff: multiplier applied to delay after each failure.
        exceptions: tuple of exception classes that should trigger a retry.
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            attempt = 1
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt >= max_attempts:
                        raise
                    time.sleep(delay)
                    delay *= backoff
                    attempt += 1

        return wrapper

    return decorator

import time
import functools
import logging

logger = logging.getLogger('tfm.retry')

def retry(max_attempts=3, initial_delay=1.0, backoff=2.0, exceptions=(Exception,)):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            attempt = 0
            while True:
                try:
                    return fn(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.exception(f"Function {fn.__name__} failed after {attempt} attempts")
                        raise
                    logger.warning(f"Retry {attempt}/{max_attempts} for {fn.__name__}: {e}. Sleeping {delay}s")
                    time.sleep(delay)
                    delay *= backoff
        return wrapper
    return decorator
