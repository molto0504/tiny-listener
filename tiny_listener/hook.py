import asyncio
from abc import ABCMeta
from functools import wraps
from inspect import Parameter, isclass, signature
from typing import Any, Callable

from ._typing import CoroutineFunc, HookFunc
from .context import Event


class _Hook(metaclass=ABCMeta):
    def __init__(self, fn: CoroutineFunc) -> None:
        self.__fn: CoroutineFunc = fn
        self.__hook: HookFunc = self.as_hook()

    def as_hook(self) -> HookFunc:
        @wraps(self.__fn)
        async def f(event: "Event") -> None:
            args = []
            kwargs = {}
            ctx = event.ctx
            for name, param in signature(self.__fn).parameters.items():
                depends = param.default
                actual = None
                if isinstance(depends, Depends):
                    if depends.use_cache and depends in ctx.cache:
                        actual = ctx.cache.get(depends)
                    else:
                        actual = await depends(event)
                        ctx.cache[depends] = actual
                elif isclass(param.annotation) and issubclass(param.annotation, Event):
                    actual = event

                if param.kind == Parameter.KEYWORD_ONLY:
                    kwargs[name] = actual
                else:
                    args.append(actual)
            return await self.__fn(*args, **kwargs)

        return f

    async def __call__(self, event: "Event") -> Any:
        return await self.__hook(event)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__hook.__name__})"

    def __hash__(self) -> int:
        return hash(self.__fn)

    def __eq__(self, other: Any) -> bool:
        return hash(self) == hash(other)


class Hook(_Hook):
    pass


class Depends(_Hook):
    def __init__(self, fn: Callable, use_cache: bool = True) -> None:
        super().__init__(fn)
        self.use_cache = use_cache


def depend(fn: Callable[..., Any], use_cache: bool = True) -> Any:
    return Depends(fn, use_cache)


def check_callback(fn: Callable) -> None:
    if not asyncio.iscoroutinefunction(fn):
        raise TypeError(
            """Hook must be a coroutine function, Such as:

    @app.on_event()
    async def foo():
        ...
"""
        )
