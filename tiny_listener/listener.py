import asyncio
import sys
import threading
from functools import wraps
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from uuid import uuid4

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

CTXType = TypeVar("CTXType", bound=Context)


Callback = Callable[..., Awaitable[Any]]


def check_hook(fn: Callable) -> Callback:
    # todo impl
    @wraps(fn)
    async def wrapper(f: Callable, *args: Any, **kwargs: Any) -> Any:
        if not asyncio.iscoroutinefunction(f):
            raise TypeError("Hook must be a coroutine function")
        return await fn(f, *args, **kwargs)

    return wrapper


class Listener(Generic[CTXType]):
    _instances: Dict[int, "Listener"] = {}

    def __init__(self) -> None:
        self.ctxs: Dict[str, CTXType] = {}
        self.routes: Dict[str, Route] = {}

        self.__startup: List[Callback] = []
        self.__shutdown: List[Callback] = []
        self.__middleware_before_event: List[Hook] = []
        self.__middleware_after_event: List[Hook] = []
        self.__error_handlers: List[Tuple[Type[Exception], Hook]] = []
        self.__context_cls: Type = Context

    def set_context_cls(self, kls: Type[Context]) -> None:
        """
        :param kls: Context class
        """
        assert issubclass(kls, Context), "kls must inherit from Context"
        self.__context_cls = kls

    async def listen(self) -> None:
        raise NotImplementedError()

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

        if cid not in self.ctxs:
            ctx = self.__context_cls(self, cid=cid, scope=scope)
            self.ctxs[ctx.cid] = ctx
            return ctx

        raise ContextAlreadyExists(f"Context `{cid}` already exist")

    def get_ctx(self, cid: str) -> CTXType:
        """
        :raises: ContextNotFound
        """
        if cid not in self.ctxs:
            raise ContextNotFound(f"Context `{cid}` not found")
        return self.ctxs[cid]

    def add_startup_callback(self, fn: Callback) -> None:
        self.__startup.append(fn)

    def add_shutdown_callback(self, fn: Callback) -> None:
        self.__shutdown.append(fn)

    def add_before_event_hook(self, fn: Callable) -> None:
        self.__middleware_before_event.append(Hook(fn))

    def add_after_event_hook(self, fn: Callback) -> None:
        self.__middleware_after_event.append(Hook(fn))

    def add_on_error_hook(self, fn: Callable, exc: Type[Exception]) -> None:
        self.__error_handlers.append((exc, Hook(fn)))

    def add_on_event_hook(
        self,
        fn: Callable,
        path: str = "{_:path}",
        after: Union[None, str, Callable, List[Union[str, Callable]]] = None,
        **opts: Any,
    ) -> None:
        name = fn.__name__
        if name in self.routes:
            raise EventAlreadyExists(f"Event `{name}` already exists")
        self.routes[name] = Route(name=name, path=path, fn=fn, after=after or [], opts=opts)

    def remove_on_event_hook(self, name: Union[str, Callable]) -> bool:
        """
        :param name: Event name or callback function
        """
        try:
            del self.routes[str(name)]
            return True
        except KeyError:
            return False

    def on_event(
        self,
        name: str = "{_:path}",
        after: Union[None, str, Callable, List[Union[str, Callable]]] = None,
        **opts: Any,
    ) -> Callable[[Hook], None]:
        def _decorator(fn: Callable) -> None:
            self.add_on_event_hook(fn, name, after, **opts)

        return _decorator

    def startup(self, fn: Callable) -> Callable:
        self.add_startup_callback(fn)
        return fn

    def shutdown(self, fn: Callable) -> Callable:
        self.add_shutdown_callback(fn)
        return fn

    def before_event(self, fn: Callable) -> Callable:
        self.add_before_event_hook(fn)
        return fn

    def after_event(self, fn: Callable) -> Callable:
        self.add_after_event_hook(fn)
        return fn

    def on_error(self, exc: Type[Exception]) -> Callable[[Callable], Callable]:
        def f(fn: Callable) -> Callable:
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
        ctx = self.new_ctx() if cid not in self.ctxs else self.ctxs[cid]
        route, params = self.match_route(name)
        event = ctx.new_event(name=name, timeout=timeout, route=route, data=data or {}, params=params)

        async def _trigger() -> None:
            try:
                for evt in event.after:
                    await evt.wait_until_done(evt.timeout)
                for fn in self.__middleware_before_event:
                    await fn(event)
                await event()
                for fn in self.__middleware_after_event:
                    await fn(event)
            except Exception as e:
                event.error = e
                handlers = [fn for kls, fn in self.__error_handlers if isinstance(e, kls)]
                if not handlers:
                    raise e
                else:
                    [await handler(event) for handler in handlers]
            finally:
                if not event.prevent_done:
                    event.done()

        return asyncio.get_event_loop().create_task(_trigger())

    @staticmethod
    def stop() -> None:
        loop = asyncio.get_event_loop()
        loop.stop()

    def exit(self) -> None:
        """Override this method to change how the app exit."""
        self.stop()
        loop = asyncio.get_event_loop()
        for fn in self.__shutdown:
            loop.run_until_complete(fn())
        sys.exit()

    @staticmethod
    def is_main_thread() -> bool:
        return threading.current_thread() is threading.main_thread()

    def setup_event_loop(self) -> asyncio.AbstractEventLoop:
        """Override this method to change default event loop"""
        if not self.is_main_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return asyncio.get_event_loop()

    def run(self) -> None:
        ident = threading.get_ident()
        if ident in Listener._instances:
            raise DuplicateListener(f"Only one instance of Listener can be run per thread, {ident=}.")

        Listener._instances[ident] = self
        try:
            loop = self.setup_event_loop()
            for fn in self.__startup:
                loop.run_until_complete(fn())
            asyncio.run_coroutine_threadsafe(self.listen(), loop)
            loop.run_forever()
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
