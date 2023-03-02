import asyncio
import signal
import threading
from typing import Any, Callable, Dict, Generic, List, Tuple, Type, TypeVar, Union
from uuid import uuid4

from ._typing import CoroFunc
from .context import Context
from .errors import (
    ContextAlreadyExists,
    ContextNotFound,
    DuplicateListener,
    EventAlreadyExists,
    EventNotFound,
    ListenerNotFound,
)
from .hook import Hook
from .routing import Params, Route
from .utils import check_coro_func, is_main_thread

CTXType = TypeVar("CTXType", bound=Context)


HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2
    signal.SIGTERM,  # Unix signal 15
)


class Listener(Generic[CTXType]):
    _instances: Dict[int, "Listener"] = {}

    def __init__(self) -> None:
        self.ctxs: Dict[str, CTXType] = {}
        self.routes: Dict[str, Route] = {}

        self.__startup: List[CoroFunc] = []
        self.__shutdown: List[CoroFunc] = []
        self.__middleware_before_event: List[Hook] = []
        self.__middleware_after_event: List[Hook] = []
        self.__error_handlers: List[Tuple[Type[Exception], Hook]] = []
        self.__context_cls: Type = Context
        self.__exiting = asyncio.Event()

    async def listen(self) -> None:
        raise NotImplementedError()

    def install_signal_handlers(self) -> None:
        if not is_main_thread():  # pragma: no cover
            return

        loop = asyncio.get_event_loop()
        for sig in HANDLED_SIGNALS:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.graceful_shutdown(sig)))

    async def graceful_shutdown(self, _: int) -> None:
        loop = asyncio.get_event_loop()
        if self.__exiting.is_set():
            loop.stop()
            return

        self.__exiting.set()
        for cb in self.__shutdown:
            await cb()
        tasks = []
        for task in asyncio.all_tasks(loop):
            if task is not asyncio.current_task(loop):
                task.cancel()
                tasks.append(task)
        await asyncio.gather(*tasks)

    def set_context_cls(self, kls: Type[Context]) -> None:
        """
        :param kls: Context class
        """
        assert issubclass(kls, Context), "kls must inherit from Context"
        self.__context_cls = kls

    def new_ctx(
        self,
        cid: Union[str, None] = None,
        scope: Union[Dict[str, Any], None] = None,
    ) -> CTXType:
        """Create a new context with the given cid and scope.

        :param cid: Context ID
        :param scope: Context scope
        :raises: ContextAlreadyExists
        """
        if cid is None:
            cid = str(uuid4())

        if scope is None:
            scope = {}

        if cid in self.ctxs:
            raise ContextAlreadyExists(f"Context `{cid}` already exist")

        ctx = self.__context_cls(self, cid=cid, scope=scope)
        self.ctxs[ctx.cid] = ctx
        return ctx

    def get_ctx(self, cid: str) -> CTXType:
        """
        :raises: ContextNotFound
        """
        if cid not in self.ctxs:
            raise ContextNotFound(f"Context `{cid}` not found")
        return self.ctxs[cid]

    def get_route(self, name: str) -> Route:
        """
        :raises: EventNotFound
        """
        if name not in self.routes:
            raise EventNotFound(f"Event `{name}` not found")
        return self.routes[name]

    def add_startup_callback(self, fn: CoroFunc) -> None:
        self.__startup.append(fn)

    def add_shutdown_callback(self, fn: CoroFunc) -> None:
        self.__shutdown.append(fn)

    def add_before_event_hook(self, fn: CoroFunc) -> None:
        self.__middleware_before_event.append(Hook(fn))

    def add_after_event_hook(self, fn: CoroFunc) -> None:
        self.__middleware_after_event.append(Hook(fn))

    def add_on_error_hook(self, fn: CoroFunc, exc: Type[Exception]) -> None:
        self.__error_handlers.append((exc, Hook(fn)))

    def add_on_event_hook(
        self,
        fn: CoroFunc,
        path: str = "{_:path}",
        **opts: Any,
    ) -> None:
        name = fn.__name__
        if name in self.routes:
            raise EventAlreadyExists(f"Event `{name}` already exists")
        self.routes[name] = Route(name=name, path=path, fn=fn, opts=opts)

    def remove_on_event_hook(self, name: Union[str, CoroFunc]) -> bool:
        """
        :param name: Event name or callback function
        """
        try:
            name = name.__name__ if callable(name) else name
            del self.routes[name]
            return True
        except KeyError:
            return False

    def on_event(
        self,
        name: str = "{_:path}",
        **opts: Any,
    ) -> Callable[[CoroFunc], CoroFunc]:
        def _decorator(fn: CoroFunc) -> CoroFunc:
            check_coro_func(fn)
            self.add_on_event_hook(fn, name, **opts)
            return fn

        return _decorator

    def startup(self, fn: CoroFunc) -> CoroFunc:
        check_coro_func(fn)
        self.add_startup_callback(fn)
        return fn

    def shutdown(self, fn: CoroFunc) -> CoroFunc:
        check_coro_func(fn)
        self.add_shutdown_callback(fn)
        return fn

    def before_event(self, fn: CoroFunc) -> CoroFunc:
        check_coro_func(fn)
        self.add_before_event_hook(fn)
        return fn

    def after_event(self, fn: CoroFunc) -> CoroFunc:
        check_coro_func(fn)
        self.add_after_event_hook(fn)
        return fn

    def on_error(self, exc: Type[Exception]) -> Callable[[CoroFunc], CoroFunc]:
        def f(fn: CoroFunc) -> CoroFunc:
            check_coro_func(fn)
            self.add_on_error_hook(fn, exc)
            return fn

        return f

    def match_route(self, path: str) -> Tuple[Route, Params]:
        """
        :raises: EventNotFound
        """
        for route in self.routes.values():
            params = route.match(path)
            if params is not None:
                return route, params
        raise EventNotFound(f"route `{path}` not found")

    def trigger_event(
        self,
        name: str,
        cid: Union[str, None] = None,
        timeout: Union[float, None] = None,
        data: Union[Dict, None] = None,
    ) -> asyncio.Task:
        """
        :raises EventNotFound:
        :raises EventAlreadyExists:
        """
        route, params = self.match_route(name)
        ctx = self.new_ctx() if cid not in self.ctxs else self.ctxs[cid]
        event = ctx.new_event(route, data or {}, params)

        async def _trigger() -> None:
            try:
                for f in self.__middleware_before_event:
                    await f(event)
                await asyncio.wait_for(event(), timeout=timeout)
                for f in self.__middleware_after_event:
                    await f(event)
            except Exception as e:
                event.error = e
                handlers = [fn for kls, fn in self.__error_handlers if isinstance(e, kls)]
                if not handlers:
                    raise e
                else:
                    [await handler(event) for handler in handlers]
            finally:
                if event.auto_done:
                    event.done()

        return asyncio.get_event_loop().create_task(_trigger())

    @staticmethod
    def setup_event_loop() -> asyncio.AbstractEventLoop:
        """Override this method to change default event loop"""
        if not is_main_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return asyncio.get_event_loop()

    async def main(self) -> None:
        for fn in self.__startup:
            await fn()
        await self.listen()
        await self.__exiting.wait()

    def run(self) -> None:
        ident = threading.get_ident()
        if ident in Listener._instances:
            raise DuplicateListener(f"Only one instance of Listener can be run per thread, {ident=}.")

        Listener._instances[ident] = self
        try:
            loop = self.setup_event_loop()
            self.install_signal_handlers()
            loop.run_until_complete(self.main())
        except asyncio.CancelledError:
            pass
        finally:
            del Listener._instances[ident]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(routes_count={len(self.routes)})"


def get_current_running_listener() -> Listener:
    """
    :raises ListenerNotFound:
    """
    ident = threading.get_ident()
    try:
        return Listener._instances[ident]  # noqa
    except KeyError as e:
        raise ListenerNotFound(f"Running Listener not found for current thread, {ident=}") from e
