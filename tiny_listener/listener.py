import asyncio
import signal
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from typing_extensions import Protocol

from .context import Context
from .hook import Hook
from .routing import Params, Route


class Fire(Protocol):
    def __call__(self,
                 name: str,
                 cid: Optional[str] = None,
                 timeout: Optional[float] = None,
                 data: Optional[Dict] = None) -> asyncio.Task: ...


class RouteNotFound(BaseException):
    pass


class ContextNotFound(BaseException):
    pass


class Listener:
    def __init__(self):
        self.ctxs: Dict[str, Context] = {}
        self.routes: List[Route] = []
        self._pre_do: List[Hook] = []
        self._post_do: List[Hook] = []
        self._error_raise: List[Tuple[Hook, Type[BaseException]]] = []

    def new_ctx(self,
                cid: str = "__global__",
                scope: Optional[Dict[str, Any]] = None) -> Context:
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

    @staticmethod
    def exception_handler(loop, context):
        if isinstance(context.get("exception"), asyncio.CancelledError):
            loop.stop()
        else:
            loop.default_exception_handler(context)

    def exit(self, *_) -> None:
        """Override this method to change how the app exit."""
        loop = asyncio.get_event_loop()
        loop.stop()

    # def pre_do(self, fn: Hook) -> None:
    #     self._pre_do.append(as_hook(fn))
    #
    # def post_do(self, fn: Hook) -> None:
    #     self._post_do.append(as_hook(fn))

    # def error_raise(self, exc: Type[BaseException]) -> Callable[[Hook], None]:
    #     def f(fn: Hook) -> None:
    #         self._error_raise.append((as_hook(fn), exc))
    #     return f

    def match_route(self, name: str) -> Tuple[Route, Params]:
        for route in self.routes:
            params = route.match(name)
            if params is not None:
                return route, params
        raise RouteNotFound(f"route `{name}` not found")

    def fire(self,
             name: str,
             cid: Optional[str] = None,
             timeout: Optional[float] = None,
             data: Optional[Dict] = None) -> asyncio.Task:
        """
        :raises: RouteNotFound
        """
        ctx = self.new_ctx(cid)
        route, params = self.match_route(name)
        event = ctx.new_event(name=name,
                              timeout=timeout,
                              route=route,
                              data=data or {},
                              params=params)

        async def _fire():
            try:
                [await evt.wait_until_done(evt.timeout) for evt in event.after]
                # [await fn(event) for fn in self._pre_do]
                await event(event)
                # [await fn(event) for fn in self._post_do]
            except BaseException as e:
                if not self._error_raise:
                    raise e
                event.error = e
                [await fn(event) for fn, exc_cls in self._error_raise if isinstance(e, exc_cls)]
            finally:
                event.done()

        return asyncio.get_event_loop().create_task(_fire())

    async def listen(self):
        raise NotImplementedError()

    def install_signal_handlers(self) -> None:
        """Override this method to install your own signal handlers ."""
        if threading.current_thread() is not threading.main_thread():
            return

        loop = asyncio.get_event_loop()

        for sig in [signal.SIGINT, signal.SIGTERM]:
            loop.add_signal_handler(sig, self.exit, sig, None)

    def set_event_loop(self):
        """Override this method to change default event loop"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    def run(self) -> None:
        """Override this method to change how the app run."""
        self.set_event_loop()
        self.install_signal_handlers()
        loop = asyncio.get_event_loop()
        asyncio.run_coroutine_threadsafe(self.listen(), loop)
        loop.run_forever()

    def on_event(self,
                 path: str = "{_:path}",
                 after: Union[None, str, List[str]] = None,
                 **kwargs: Any) -> Callable[[Hook], None]:
        def _decorator(fn: Hook) -> None:
            self.routes.append(Route(path=path,
                                     fn=fn,
                                     after=after or [],
                                     opts=kwargs))

        return _decorator

    def __repr__(self) -> str:
        return "{}(routes_count={})".format(self.__class__.__name__, len(self.routes))
