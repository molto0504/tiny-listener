import asyncio
import signal
from inspect import signature, Parameter
from functools import wraps
from typing import Optional, Dict, Callable, List, Any, Union, Tuple, Type, Awaitable
from typing_extensions import Protocol

from .context import Context, Event
from .routing import Route
from .dependant import Depends


class Params(dict):
    pass


class Fire(Protocol):
    def __call__(self, name: str, cid: Optional[str] = None, timeout: Optional[float] = None, data: Optional[Dict] = None) -> asyncio.Task: ...


Hook = Callable[..., Awaitable[None]]
WrappedHook = Callable[['Context', 'Event', Params, Optional[BaseException]], Awaitable[None]]


class RouteNotFound(BaseException):
    pass


class ContextNotFound(BaseException):
    pass


class Listener:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.loop.set_exception_handler(self.exception_handler)
        for sig in [signal.SIGINT, signal.SIGTERM]:
            self.loop.add_signal_handler(sig, self.exit)

        self.ctxs: Dict[str, Context] = {}
        self.routes: List[Route] = []
        self._pre_do: List[WrappedHook] = []
        self._post_do: List[WrappedHook] = []
        self._error_raise: List[Tuple[WrappedHook, Type[BaseException]]] = []

    def new_ctx(self, cid: str = "__main__", scope: Optional[Dict] = None) -> Context:
        try:
            ctx = self.get_ctx(cid)
        except ContextNotFound:
            ctx = Context(listener=self, cid=cid, scope=scope)
            self.ctxs[cid] = ctx
        return ctx

    def get_ctx(self, cid: str) -> Context:
        try:
            return self.ctxs[cid]
        except KeyError:
            raise ContextNotFound(f"Context `{cid}` not found")

    def drop_ctx(self, cid) -> 'Context':
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

    def exit(self) -> None:
        tasks = asyncio.gather(*asyncio.Task.all_tasks(self.loop), loop=self.loop, return_exceptions=True)
        tasks.add_done_callback(lambda t: self.loop.stop())
        tasks.cancel()

    def pre_do(self, fn: Hook) -> None:
        self._pre_do.append(wrap_hook(fn))

    def post_do(self, fn: Hook) -> None:
        self._post_do.append(wrap_hook(fn))

    def error_raise(self, exc: Type[BaseException]) -> Callable[[Hook], None]:
        def f(fn: Hook) -> None:
            self._error_raise.append((wrap_hook(fn), exc))
        return f

    def match_route(self, name: str) -> Tuple[Route, Params]:
        for r in self.routes:
            result, params = r.match(name)
            if result:
                return r, Params(params)
        raise RouteNotFound(f"route `{name}` not found")

    def fire(
            self,
            name: str,
            cid: Optional[str] = None,
            timeout: Optional[float] = None,
            data: Optional[Dict] = None
    ) -> asyncio.Task:
        async def _fire():
            ctx = self.new_ctx(cid)
            event = ctx.new_event(name=name, timeout=timeout, route=None, data=data or {})
            params = Params()
            try:
                event.route, params = self.match_route(name)
                [await asyncio.wait_for(evt.wait(), evt.timeout) for evt in event.parents]
                [await fn(ctx, event, params, None) for fn in self._pre_do]
                await event.route.fn(ctx, event, params, None)
                [await fn(ctx, event, params, None) for fn in self._post_do]
            except BaseException as e:
                if not self._error_raise:
                    raise e
                [await fn(ctx, event, params, e) for fn, exc_cls in self._error_raise if isinstance(e, exc_cls)]
            finally:
                if event:
                    event.done()

        return self.loop.create_task(_fire())

    async def listen(self, fire: Fire):
        raise NotImplementedError()

    def run(self) -> None:
        self.loop.create_task(self.listen(self.fire))
        self.loop.run_forever()

    def do(
            self,
            path: str,
            parents: Union[None, List[str], Callable[[Context], List[str]]] = None,
            **kwargs: Any
    ) -> Callable[[Hook], None]:
        def _decorator(fn: Hook) -> None:
            self.routes.append(Route(path=path, fn=wrap_hook(fn), parents=parents or [], opts=kwargs))
        return _decorator

    def __repr__(self) -> str:
        return "{}(listener_count={})".format(self.__class__.__name__, len(self.routes))


def wrap_hook(handler: Hook) -> WrappedHook:
    @wraps(handler)
    async def f(ctx: Context, event: Event, params: Params, exc: Optional[BaseException] = None) -> None:
        args = []
        kwargs = {}
        # TODO ignore KEYWORD_ONLY
        for name, param in signature(handler).parameters.items():
            if param.kind == Parameter.KEYWORD_ONLY:
                depends = param.default
                if param.default and isinstance(depends, Depends):
                    if depends.use_cache and ctx.cache.exist(depends):
                        kwargs[name] = ctx.cache.get(depends)
                        continue
                    res = await wrap_hook(depends.dependency)(ctx, event, params, None)
                    kwargs[name] = res
                    ctx.cache.set(depends, res)
                    continue
                kwargs[name] = None
                continue

            if param.annotation is Context:
                args.append(ctx)
            elif param.annotation is Event:
                args.append(event)
            elif param.annotation is Params:
                args.append(params)
            elif issubclass(param.annotation, BaseException):
                args.append(exc)
            else:
                args.append(None)
        return await handler(*args, **kwargs)
    return f
