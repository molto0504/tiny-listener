import asyncio
import signal
from typing import Optional, Dict, Callable, List, Any, Union, Tuple, Type
from copy import copy

from .context import Context
from .routing import Route, _EventHandler, EventHandler, as_handler, Params


class RouteNotFound(BaseException):
    pass


class ContextNotFound(BaseException):
    pass


class DuplicatedCid(BaseException):
    pass


class Listener:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.loop.set_exception_handler(self.exception_handler)
        for sig in [signal.SIGINT, signal.SIGTERM]:
            self.loop.add_signal_handler(sig, self.exit)

        self.ctxs: Dict[str, Context] = {}
        self.routes: List[Route] = []
        self._pre_do: List[EventHandler] = []
        self._post_do: List[EventHandler] = []
        self._error_raise: List[Tuple[EventHandler, Type[BaseException]]] = []

    def new_ctx(self, cid: str = "__main__", scope: Optional[Dict] = None) -> Context:
        if self.get_ctx(cid):
            raise DuplicatedCid(f"Context `{cid}` already exist")

        ctx = Context(listener=self, cid=cid, scope=scope)
        self.ctxs[cid] = ctx
        return ctx

    def get_ctx(self, cid: str) -> Optional[Context]:
        return self.ctxs.get(cid)


    # def is_context_exist(self, cid: str) -> bool:
    #     return self.ctxs.get(cid) is not None


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
            parents_timeout: Optional[float] = None,
            data: Optional[Dict] = None
    ):
        async def _fire():
            ctx = self.new_ctx(cid)
            params = Params()
            route = None
            for r in self.routes:
                result, params = r.match(name)
                if result:
                    route = r
                    params = Params(params)
                    break
            event = ctx.new_event(name=name, parents_timeout=parents_timeout, route=route, **data or {})

            async with event as exc:
                try:
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
                    event.error = e
                    [await fn(ctx, event, params, e) for fn, exc_cls in self._error_raise if isinstance(e, exc_cls)]
                    if event.error is not None:
                        ctx.drop(cid)

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

    def __repr__(self) -> str:
        return "{}(listener_count={})".format(self.__class__.__name__, len(self.routes))
