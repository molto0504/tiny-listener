import asyncio
import signal
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from typing_extensions import Protocol

from .context import Context
from .dependant import Hook
from .routing import Route, Params


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

    def install_signal_handlers(self) -> None:
        if threading.current_thread() is not threading.main_thread():
            return

        loop = asyncio.get_event_loop()

        for sig in [signal.SIGINT, signal.SIGTERM]:
            loop.add_signal_handler(sig, self.exit, sig, None)

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

    def drop_ctx(self, cid: str) -> 'Context':
        try:
            return self.ctxs.pop(cid)
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
                [await evt.wait_until_done(evt.timeout) for evt in event.parents]
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

    async def listen(self, fire: Fire):
        raise NotImplementedError()

    def run(self) -> None:
        """Override this method to change how the app run."""
        self.install_signal_handlers()
        loop = asyncio.get_event_loop()
        loop.create_task(self.listen(self.fire))
        loop.run_forever()

    def on_event(self,
                 path: str,
                 parents: Union[None, List[str], Callable[[Context], List[str]]] = None,
                 **kwargs: Any) -> Callable[[Hook], None]:
        def _decorator(fn: Hook) -> None:
            self.routes.append(Route(path=path,
                                     fn=fn,
                                     parents=parents or [],
                                     opts=kwargs))

        return _decorator

    def __repr__(self) -> str:
        return "{}(routes_count={})".format(self.__class__.__name__, len(self.routes))

# def wrap_hook(handler: Hook) -> WrappedHook:
#     @wraps(handler)
#     async def f(ctx: Context, event: Event, params: Params, exc: Optional[BaseException] = None) -> None:
#         args = []
#         kwargs = {}
#         # TODO ignore KEYWORD_ONLY
#         for name, param in signature(handler).parameters.items():
#             if param.kind == Parameter.KEYWORD_ONLY:
#                 depends = param.default
#                 if param.default and isinstance(depends, Depends):
#                     if depends.use_cache and ctx.cache.exist(depends):
#                         kwargs[name] = ctx.cache.get(depends)
#                         continue
#                     res = await wrap_hook(depends.dependency)(ctx, event, params, None)
#                     kwargs[name] = res
#                     ctx.cache.set(depends, res)
#                     continue
#                 kwargs[name] = None
#                 continue
#
#             if param.annotation is Context:
#                 args.append(ctx)
#             elif param.annotation is Event:
#                 args.append(event)
#             elif param.annotation is Params:
#                 args.append(params)
#             elif issubclass(param.annotation, BaseException):
#                 args.append(exc)
#             else:
#                 args.append(None)
#         return await handler(*args, **kwargs)
#     return f
