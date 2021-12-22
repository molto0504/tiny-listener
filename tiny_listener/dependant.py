import asyncio
from functools import wraps
from inspect import Parameter, signature
from typing import Any, Awaitable, Callable, Union

from .context import Event


HookAble = Callable[..., Union[Awaitable[Any], Any]]
Hook = Callable[['Event'], Awaitable[Any]]


class Depends:
    def __init__(self,
                 fn: HookAble,
                 use_cache: bool = True) -> None:
        self.__fn = fn
        self.__is_coro: bool = asyncio.iscoroutinefunction(fn)
        self.hook: Hook = as_hook(fn)
        self.use_cache = use_cache

    @property
    def is_coro(self) -> bool:
        return self.__is_coro

    async def __call__(self, event: 'Event') -> None:
        return await self.hook(event)

    def __hash__(self):
        return hash(self.__fn)

    def __eq__(self, other):
        return self.__fn == other.__fn

    def __repr__(self) -> str:
        return "{}({}, use_cache={})".format(self.__class__.__name__,
                                             self.hook.__name__,
                                             self.use_cache)


def as_hook(fn: HookAble) -> Hook:
    fn: Callable[..., Awaitable[Any]] = asyncio.coroutine(fn)

    @wraps(fn)
    async def f(event: 'Event') -> None:
        args = []
        kwargs = {}
        ctx = event.ctx
        for name, param in signature(fn).parameters.items():
            # TODO ignore KEYWORD_ONLY
            if param.kind == Parameter.KEYWORD_ONLY:
                depends: Union[Any, Depends] = param.default
                if not isinstance(depends, Depends):
                    kwargs[name] = None
                    continue

                if depends.use_cache and depends in ctx.cache:
                    kwargs[name] = ctx.cache.get(depends)
                    continue

                res = await depends(event)
                kwargs[name] = res
                ctx.cache[depends] = res
                continue

            if param.annotation is Event:
                args.append(event)
                continue

            args.append(None)
        return await fn(*args, **kwargs)
    return f
