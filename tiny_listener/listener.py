import asyncio
import sys
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Type, Union

from .context import Context
from .hook import Hook
from .routing import Params, Route


class RouteNotFound(BaseException):
    pass


class ContextNotFound(BaseException):
    pass


class Listener:
    def __init__(self):
        self.ctxs: Dict[str, Context] = {}
        self.routes: List[Route] = []

        self.__startup: List[Callable[..., Awaitable[Any]]] = []
        self.__shutdown: List[Callable[..., Awaitable[Any]]] = []
        self.__middleware_before_event: List[Hook] = []
        self.__middleware_after_event: List[Hook] = []
        self.__error_handlers: List[Tuple[Type[BaseException], Hook]] = []
        self.__cid: int = 0

    @property
    def cid(self):
        self.__cid += 1
        return f"__{self.__cid}__"

    async def listen(self):
        raise NotImplementedError()

    def new_ctx(
        self, cid: Optional[str] = None, scope: Optional[Dict[str, Any]] = None
    ) -> Context:
        cid = self.cid if cid is None else cid
        try:
            ctx = self.get_ctx(cid)
        except ContextNotFound:
            ctx = Context(listener=self, cid=cid, scope=scope)
            self.add_ctx(ctx)
        return ctx

    def add_ctx(self, ctx: Context):
        self.ctxs[ctx.cid] = ctx

    def get_ctx(self, cid: str) -> Context:
        try:
            return self.ctxs[cid]
        except KeyError:
            raise ContextNotFound(f"Context `{cid}` not found")

    def on_event(
        self,
        path: str = "{_:path}",
        after: Union[None, str, List[str]] = None,
        **opts: Any,
    ) -> Callable[[Hook], None]:
        def _decorator(fn: Hook) -> None:
            self.routes.append(Route(path=path, fn=fn, after=after or [], opts=opts))

        return _decorator

    def startup(self, fn: Callable) -> Callable:
        self.__startup.append(asyncio.coroutine(fn))
        return fn

    def shutdown(self, fn: Callable) -> Callable:
        self.__shutdown.append(asyncio.coroutine(fn))
        return fn

    def before_event(self, fn: Callable) -> Callable:
        self.__middleware_before_event.append(Hook(fn))
        return fn

    def after_event(self, fn: Callable) -> Callable:
        self.__middleware_after_event.append(Hook(fn))
        return fn

    def error_handler(self, exc: Type[BaseException]) -> Callable[[Callable], Callable]:
        def f(fn: Callable) -> Callable:
            self.__error_handlers.append((exc, Hook(fn)))
            return fn

        return f

    def match_route(self, name: str) -> Tuple[Route, Params]:
        for route in self.routes:
            params = route.match(name)
            if params is not None:
                return route, params
        raise RouteNotFound(f"route `{name}` not found")

    def fire(
        self,
        name: str,
        cid: Optional[str] = None,
        timeout: Optional[float] = None,
        data: Optional[Dict] = None,
    ) -> asyncio.Task:
        """
        :raises: RouteNotFound or EventAlreadyExist
        """
        ctx = self.new_ctx(cid)
        route, params = self.match_route(name)
        event = ctx.new_event(
            name=name, timeout=timeout, route=route, data=data or {}, params=params
        )

        async def _fire():
            try:
                [await evt.wait_until_done(evt.timeout) for evt in event.after]
                [await fn(event) for fn in self.__middleware_before_event]
                await event()
                [await fn(event) for fn in self.__middleware_after_event]
            except BaseException as e:
                event.error = e
                handlers = [
                    fn for kls, fn in self.__error_handlers if isinstance(e, kls)
                ]
                if not handlers:
                    raise e
                else:
                    [await handler(event) for handler in handlers]
            finally:
                event.done()

        return asyncio.get_event_loop().create_task(_fire())

    def stop(self):
        loop = asyncio.get_event_loop()
        loop.stop()

    def exit(self) -> None:
        """Override this method to change how the app exit."""
        self.stop()
        loop = asyncio.get_event_loop()
        for fn in self.__shutdown:
            loop.run_until_complete(fn())
        sys.exit()

    def set_event_loop(
        self, loop: Optional[asyncio.AbstractEventLoop] = None
    ) -> asyncio.AbstractEventLoop:
        """Override this method to change default event loop"""
        if loop is None:
            loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

    def run(self) -> None:
        """Override this method to change how the app run."""
        loop = self.set_event_loop()
        for fn in self.__startup:
            loop.run_until_complete(fn())
        asyncio.run_coroutine_threadsafe(self.listen(), loop)
        try:
            loop.run_forever()
        except (KeyboardInterrupt, SystemExit):
            self.exit()

    def __repr__(self) -> str:
        return "{}(routes_count={})".format(self.__class__.__name__, len(self.routes))
