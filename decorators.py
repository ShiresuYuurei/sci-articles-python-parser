import random
from functools import wraps
from typing import Callable, TypeVar
import time

T = TypeVar('T')

def stage_logger(stage_name: str):
    """Декоратор для логирования этапов выполнения"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            print(f"=== {stage_name} ===")
            result = func(*args, **kwargs)
            print(f"✓ {stage_name} completed successfully.")
            return result
        return wrapper
    return decorator

def retry_on_failure(max_retries=3, delay=2):
    """Декоратор для повторных попыток вызова функции"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        print(f"Error in {func.__name__}: {e}")
                        raise
                    time.sleep(delay * (attempt + 1) * random.uniform(0.8, 1.2))
            return None
        return wrapper
    return decorator