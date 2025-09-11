from functools import wraps
from typing import Callable, TypeVar

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
