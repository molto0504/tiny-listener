import asyncio
from functools import wraps, partial
from inspect import Parameter, signature
from typing import Any, Awaitable, Callable, Union

from .context import Event


HookFunc = Callable[['Event', Any], Awaitable[Any]]


class Hook:
    def __init__(self, fn: Callable) -> None:
        self.__fn = fn
        self.__parameters = signature(fn).parameters
        self.__is_coro = asyncio.iscoroutinefunction(fn)
        self.__hook = self.as_hook()

    def as_hook(self) -> HookFunc:
        @wraps(self.__fn)
        async def f(event: 'Event', executor: Any = None) -> None:
            args = []
            kwargs = {}
            ctx = event.ctx
            for name, param in self.__parameters.items():
                if param.kind == Parameter.KEYWORD_ONLY:
                    depends: Union[Any, Depends] = param.default
                    if not isinstance(depends, Depends):
                        kwargs[name] = None
                        continue

                    if depends.use_cache and depends in ctx.cache:
                        kwargs[name] = ctx.cache.get(depends)
                        continue

                    res = await depends(event, executor)
                    kwargs[name] = res
                    ctx.cache[depends] = res
                    continue

                if param.annotation is Event:
                    args.append(event)
                    continue

                args.append(None)
            if self.__is_coro:
                return await self.__fn(*args, **kwargs)
            else:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(executor, partial(self.__fn, *args, **kwargs))
        return f

    async def __call__(self, event: 'Event', executor: Any = None) -> None:
        return await self.__hook(event, executor)

    def __repr__(self) -> str:
        return "{}({})".format(self.__class__.__name__, self.__hook.__name__)

    def __hash__(self) -> int:
        return hash(self.__fn)

    def __eq__(self, other: 'Hook') -> bool:
        return hash(self) == hash(other)


class Depends(Hook):
    def __init__(self,
                 fn: Callable,
                 use_cache: bool = True) -> None:
        super().__init__(fn)
        self.use_cache = use_cache
