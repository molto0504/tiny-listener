import asyncio
from functools import wraps
from inspect import Parameter, signature
from typing import Any, Awaitable, Callable, Union

from .context import Context, Event


Hook = Callable[['Context', 'Event'], Awaitable[None]]


class Depends:
    def __init__(self,
                 fn: Callable[..., Union[Awaitable[None], None]],
                 use_cache: bool = True) -> None:
        self.__is_coro: bool = asyncio.iscoroutinefunction(fn)
        self.hook: Hook = as_hook(fn)
        self.use_cache = use_cache

    @property
    def is_coro(self) -> bool:
        return self.__is_coro

    async def __call__(self, ctx: 'Context', event: 'Event') -> None:
        return await self.hook(ctx, event)

    def __repr__(self) -> str:
        return "{}({}, use_cache={})".format(self.__class__.__name__,
                                             self.hook.__name__,
                                             self.use_cache)


def as_hook(fn: Callable[..., Union[Awaitable[None], None]]) -> Hook:
    fn: Callable[..., Awaitable[None]] = asyncio.coroutine(fn)

    @wraps(fn)
    async def f(ctx: 'Context', event: 'Event') -> None:
        args = []
        kwargs = {}
        for name, param in signature(fn).parameters.items():
            # TODO ignore KEYWORD_ONLY
            if param.kind == Parameter.KEYWORD_ONLY:
                depends: Union[Any, Depends] = param.default
                if not isinstance(depends, Depends):
                    kwargs[name] = None
                    continue

                if depends.use_cache and depends.hook in ctx.cache:
                    kwargs[name] = ctx.cache.get(depends.hook)
                    continue

                res = await depends(ctx, event)
                kwargs[name] = res
                ctx.cache[depends.hook] = res
                continue

            if param.annotation is Context:
                args.append(ctx)
                continue

            if param.annotation is Event:
                args.append(event)
                continue

            args.append(None)
        return await fn(*args, **kwargs)
    return f
