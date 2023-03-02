import asyncio
import threading
from importlib import import_module
from typing import Any, Callable


def import_from_string(import_str: Any) -> Any:
    import_str = str(import_str)
    module_str, _, attrs_str = import_str.partition(":")
    if not module_str or not attrs_str:
        raise ImportError(f"Import string '{import_str}' must be in format '<module>:<attribute>'")

    instance = import_module(module_str)
    for attr in attrs_str.split("."):
        try:
            instance = getattr(instance, attr)
        except AttributeError as e:
            raise ImportError(f"Module '{module_str}' has no attribute '{attr}'") from e

    return instance


def is_main_thread() -> bool:
    return threading.current_thread() is threading.main_thread()


def check_coro_func(fn: Callable) -> None:
    if not asyncio.iscoroutinefunction(fn):
        raise TypeError(
            """Hook must be a coroutine function, Such as:

    @app.on_event()
    async def foo():
        ...
"""
        )
