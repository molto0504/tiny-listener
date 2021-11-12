import asyncio
import signal
from typing import Optional, Dict, Callable, List, Any, Union, Tuple, Type
from concurrent.futures import CancelledError
from copy import copy

from .context import Context
from .routing import Route, _EventHandler, EventHandler, as_handler, Params


class NotFound(BaseException):
    pass


class Listener:
    __default_routes__: List[Route] = []
    __default_pre_do__: List[EventHandler] = []
    __default_post_do__: List[EventHandler] = []
    __default_error_raise__: List[Tuple[EventHandler, Type[BaseException]]] = []

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.loop.set_exception_handler(self.exception_handler)
        for sig in [signal.SIGINT, signal.SIGTERM]:
            self.loop.add_signal_handler(sig, self.exit)

        self.routes = copy(self.__default_routes__)
        self._pre_do = copy(self.__default_pre_do__)
        self._post_do = copy(self.__default_post_do__)
        self._error_raise = copy(self.__default_error_raise__)

    def new_context(self, cid: Optional[str] = None, **scope: Any) -> Context:
        return Context(cid, _listener_=self, **scope)

    @staticmethod
    def exception_handler(loop, context):
        if isinstance(context.get("exception"), CancelledError):
            loop.stop()
        else:
            loop.default_exception_handler(context)

    def exit(self) -> None:
        tasks = asyncio.gather(*asyncio.Task.all_tasks(self.loop), loop=self.loop, return_exceptions=True)
        tasks.add_done_callback(lambda t: self.loop.stop())
        tasks.cancel()

    def pre_do(self, fn: _EventHandler) -> None:
        self._pre_do.append(as_handler(fn))

    def post_do(self, fn: _EventHandler) -> None:
        self._post_do.append(as_handler(fn))

    def error_raise(self, exc: Type[BaseException]) -> Callable[[_EventHandler], None]:
        def f(fn: _EventHandler) -> None:
            self._error_raise.append((as_handler(fn), exc))
        return f

    def fire(
            self,
            name: str,
            cid: Optional[str] = None,
            timeout: Optional[float] = None,
            data: Optional[Dict] = None
    ):
        ctx = self.new_context(cid)

        async def _fire():
            params = Params()
            route = None
            for r in self.routes:
                result, params = r.match(name)
                if result:
                    route = r
                    params = Params(params)
                    break
            event = ctx.new_event(name=name, timeout=timeout, route=route, **data or {})

            try:
                async with event as exc:
                    if event.route is None:
                        raise NotFound(f"route `{name}` not found")
                    if exc:
                        raise exc
                    [await fn(ctx, event, params, exc) for fn in self._pre_do]
                    res = await route.fn(ctx, event, params)
                    [await fn(ctx, event, params, exc) for fn in self._post_do]
                    return res
            except BaseException as e:
                if not self._error_raise:
                    raise e
                [await fn(ctx, event, params, e) for fn, exc_cls in self._error_raise if isinstance(e, exc_cls)]

        return self.loop.create_task(_fire())

    async def listen(self, fire: Callable[..., asyncio.Task]):
        raise NotImplementedError()

    def run(self) -> None:
        self.loop.create_task(self.listen(self.fire))
        self.loop.run_forever()

    def do(
            self,
            path: str,
            parents: Union[None, List[str], Callable[[Context], List[str]]] = None,
            **kwargs: Any
    ) -> Callable[[_EventHandler], None]:
        parents = parents or []

        def _decorator(fn: _EventHandler) -> None:
            self.routes.append(Route(path=path, fn=fn, parents=parents, opts=kwargs))
        return _decorator

    @classmethod
    def default_do(
            cls,
            path: str,
            parents: Union[None, List[str], Callable[[Context], List[str]]] = None,
            **kwargs: Any
    ) -> Callable[[_EventHandler], None]:
        parents = parents or []

        def _decorator(fn: _EventHandler) -> None:
            cls.__default_routes__.append(Route(path=path, fn=fn, parents=parents, opts=kwargs))
        return _decorator

    @classmethod
    def default_pre_do(cls, fn: _EventHandler) -> None:
        cls.__default_pre_do__.append(as_handler(fn))

    @classmethod
    def default_post_do(cls, fn: _EventHandler) -> None:
        cls.__default_post_do__.append(as_handler(fn))

    @classmethod
    def default_error_raise(cls, exc: Type[BaseException]) -> Callable[[_EventHandler], None]:
        def f(fn: _EventHandler) -> None:
            cls.__default_error_raise__.append((as_handler(fn), exc))
        return f

    def __repr__(self) -> str:
        return "{}(listener_count={})".format(self.__class__.__name__, len(self.routes))
