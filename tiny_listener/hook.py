import asyncio
from abc import ABCMeta
from functools import wraps
from inspect import Parameter, isclass, signature
from typing import Any, Final, Union

from ._typing import CoroFunc, HookFunc, PathParams
from .errors import PathParamsError
from .event import Event


class _Hook(metaclass=ABCMeta):
    def __init__(self, fn: CoroFunc, timeout: Union[float, None] = None) -> None:
        self.__fn: CoroFunc = fn
        self.__hook: HookFunc = self.as_hook()
        self.timeout: Final = timeout

    def as_hook(self) -> HookFunc:
        @wraps(self.__fn)
        async def f(event: "Event", params: PathParams) -> None:
            args = []
            kwargs = {}
            ctx = event.ctx
            for name, param in signature(self.__fn).parameters.items():
                default = param.default
                anno = param.annotation

                actual = None
                if isinstance(default, Depends):
                    if default.use_cache and default in ctx.cache:
                        actual = ctx.cache.get(default)
                    else:
                        actual = await asyncio.wait_for(default(event, params), timeout=default.timeout)
                        ctx.cache[default] = actual
                elif isclass(anno) and issubclass(anno, Event):
                    actual = event
                elif anno is Param:
                    try:
                        actual = params[name]
                    except KeyError as e:
                        raise PathParamsError(f"Path param `{name}` is invalid, allowed: {params.keys()}") from e
                if param.kind == Parameter.KEYWORD_ONLY:
                    kwargs[name] = actual
                else:
                    args.append(actual)
            return await self.__fn(*args, **kwargs)

        return f

    async def __call__(self, event: "Event", params: PathParams) -> Any:
        return await self.__hook(event, params)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__hook.__name__})"

    def __hash__(self) -> int:
        return hash(self.__fn)

    def __eq__(self, other: Any) -> bool:
        return hash(self) == hash(other)


class Hook(_Hook):
    pass


class Depends(_Hook):
    def __init__(self, fn: CoroFunc, use_cache: bool = True, timeout: Union[float, None] = None) -> None:
        super().__init__(fn, timeout)
        self.use_cache = use_cache


def depend(fn: CoroFunc, use_cache: bool = True, timeout: Union[float, None] = None) -> Any:
    return Depends(fn, use_cache, timeout)


Param: Any = object()
"""use this to inject a path param"""
