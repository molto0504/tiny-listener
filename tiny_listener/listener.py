import re
import asyncio
import signal
from typing import Optional, Dict, Callable, List, Awaitable, NamedTuple, Any, Union, Coroutine
from inspect import signature, Parameter
from functools import wraps

from .context import Context, Event


_EventHandler = Callable[..., Awaitable[None]]
EventHandler = Callable[[Context, Event], Awaitable[None]]


def inject(handler: _EventHandler) -> EventHandler:
    @wraps(handler)
    async def f(ctx: Context, event: Event) -> None:
        args = []
        kwargs = {}
        for name, param in signature(handler).parameters.items():
            if param.kind == Parameter.KEYWORD_ONLY:
                kwargs[name] = None
            elif param.annotation is Context:
                args.append(ctx)
            elif param.annotation is Event:
                args.append(event)
            else:
                args.append(None)
        return await handler(*args, **kwargs)
    return f


class Handler(NamedTuple):
    fn: EventHandler
    opts: Dict[str, Any]


class Listener:
    __todos__ = []

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.handlers: Dict[str, Handler] = {}
        for sig in [signal.SIGINT, signal.SIGTERM]:
            self.loop.add_signal_handler(sig, self.__exit)

        self._pre_send: List[EventHandler] = []
        self._post_send: List[EventHandler] = []
        self._error_raise: List[EventHandler] = []

    def new_context(self, cid: Optional[str] = None, **scope: Any) -> Context:
        return Context(cid, _listener_=self, **scope)

    def __exit(self) -> None:
        for t in asyncio.Task.all_tasks(self.loop):
            t.cancel()

    def pre_send(self, handler: _EventHandler) -> None:
        self._pre_send.append(inject(handler))

    def post_send(self, handler: _EventHandler) -> None:
        self._post_send.append(inject(handler))

    def error_raise(self, handler: _EventHandler) -> None:
        self._error_raise.append(inject(handler))

    def todo(self, name: str, cid: Optional[str] = None, block: bool = False, **detail: Any) -> Optional[Coroutine]:
        handler = None
        for pat, val in self.handlers.items():
            if re.match(pat, name):
                handler = val
                break
        assert handler, f"handler `{name}` not found"

        ctx = self.new_context(cid)
        if name not in ctx.events:
            event = ctx.new_event(name)
        else:
            event = ctx.events[name]

        event.parents_count = handler.opts.get("parents_count")
        event.add_parents(*handler.opts["parents"]).set_detail(**detail)

        async def _todo():
            async with event:
                [await fn(ctx, event) for fn in self._pre_send]
                try:
                    return await handler.fn(ctx, event)
                except BaseException as e:
                    if not self._error_raise:
                        raise e
                    ctx.errors.append(e)
                    [await fn(ctx, event) for fn in self._error_raise]
                [await fn(ctx, event) for fn in self._post_send]

        if block:
            return _todo()
        else:
            self.loop.create_task(_todo())

    async def listen(self, todo: Callable[..., None]):
        raise NotImplementedError()

    async def main_loop(self) -> None:
        try:
            await self.listen(self.todo)
        except asyncio.CancelledError:
            pass

    def run(self, forever: bool = False) -> None:
        self.loop.run_until_complete(self.main_loop())
        if forever:
            self.loop.run_forever()
        tasks = asyncio.gather(*asyncio.Task.all_tasks(self.loop))
        if not tasks.done():
            self.loop.run_until_complete(tasks)

    def do(
            self,
            pattern: str,
            parents: Union[None, List[str], Callable[[Context], List[str]]] = None,
            parents_count: Optional[int] = None,
            **kwargs: Any
    ) -> Callable[[_EventHandler], None]:
        parents = parents or []

        def _decorator(fn: _EventHandler) -> None:
            assert pattern not in self.handlers
            self.handlers[pattern] = Handler(fn=inject(fn), opts={"parents": parents, "parents_count": parents_count, **kwargs})
        return _decorator

    def __repr__(self) -> str:
        return "{}(listener_count={})".format(self.__class__.__name__, len(self.handlers))
