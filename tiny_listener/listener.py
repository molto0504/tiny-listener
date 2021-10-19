import asyncio
import signal
from typing import Optional, Dict, Callable, List, Any, Union, Coroutine

from .context import Context
from .routing import Route, _EventHandler, EventHandler, inject, Params


class Listener:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.routes: List[Route] = []
        for sig in [signal.SIGINT, signal.SIGTERM]:
            self.loop.add_signal_handler(sig, self.__exit)

        self._pre_do: List[EventHandler] = []
        self._post_do: List[EventHandler] = []
        self._error_raise: List[EventHandler] = []

    def new_context(self, cid: Optional[str] = None, **scope: Any) -> Context:
        return Context(cid, _listener_=self, **scope)

    def __exit(self) -> None:
        for t in asyncio.Task.all_tasks(self.loop):
            t.cancel()

    def pre_do(self, handler: _EventHandler) -> None:
        self._pre_do.append(inject(handler))

    def post_do(self, handler: _EventHandler) -> None:
        self._post_do.append(inject(handler))

    def error_raise(self, handler: _EventHandler) -> None:
        self._error_raise.append(inject(handler))

    def todo(self, name: str, cid: Optional[str] = None, block: bool = False, data: Optional[Dict] = None) -> Coroutine or None:
        route = None
        params = {}
        for r in self.routes:
            result, params = r.match(name)
            if result:
                route = r
                break
        assert route, f"handler `{name}` not found"
        params = Params(params)

        ctx = self.new_context(cid)
        event = ctx.new_event(name)
        event.parents_count = route.opts.get("parents_count")
        event.add_parents(*route.opts["parents"]).set_data(data or {})

        async def _todo():
            async with event:
                [await fn(ctx, event, params) for fn in self._pre_do]
                try:
                    return await route.fn(ctx, event, params)
                except BaseException as e:
                    if not self._error_raise:
                        raise e
                    ctx.errors.append(e)
                    [await fn(ctx, event, params) for fn in self._error_raise]
                [await fn(ctx, event, params) for fn in self._post_do]

        if block:
            return _todo()
        else:
            self.loop.create_task(_todo())

    async def listen(self, todo: Callable[..., Coroutine or None]):
        raise NotImplementedError()

    def run(self) -> None:
        self.loop.create_task(self.listen(self.todo))
        self.loop.run_forever()

    def do(
            self,
            path: str,
            parents: Union[None, List[str], Callable[[Context], List[str]]] = None,
            parents_count: Optional[int] = None,
            **kwargs: Any
    ) -> Callable[[_EventHandler], None]:
        parents = parents or []

        def _decorator(fn: _EventHandler) -> None:
            assert path not in self.routes
            self.routes.append(Route(path=path, fn=fn, opts={"parents": parents, "parents_count": parents_count, **kwargs}))
        return _decorator

    def __repr__(self) -> str:
        return "{}(listener_count={})".format(self.__class__.__name__, len(self.routes))
