import re
import asyncio
import signal
from typing import Optional, Dict, Callable, List, Awaitable, NamedTuple, Any, Union
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

    def todo(self, name: str, cid: Optional[str] = None, **detail: Any) -> None:
        assert name in self.__todos__, f"todo `{name}` not found"

        handler = None
        for pat, val in self.handlers.items():
            if re.match(pat, name):
                handler = val
                break
        assert handler, f"handler `{name}` not found"  # TODO 404

        ctx = self.new_context(cid)
        event = ctx.events[name].with_parent(*handler.opts["after"]).with_detail(**detail)

        async def _todo():
            async with event:
                [await fn(ctx, event) for fn in self._pre_send]
                try:
                    await handler.fn(ctx, event)
                except BaseException as e:
                    if not self._error_raise:
                        raise e
                    ctx.errors.append(e)
                    [await fn(ctx, event) for fn in self._error_raise]
                [await fn(ctx, event) for fn in self._post_send]

        self.loop.create_task(_todo())

    async def listen(self, todo: Callable[[str], None]):
        raise NotImplementedError()

    async def main_loop(self) -> None:
        try:
            await self.listen(self.todo)
        except asyncio.CancelledError:
            pass

    def run(self) -> None:
        self.loop.run_until_complete(self.main_loop())
        tasks = asyncio.gather(*asyncio.Task.all_tasks(self.loop))
        if not tasks.done():
            self.loop.run_until_complete(tasks)

    def do(
            self,
            pattern: str,
            after: Union[None, List[str], Callable[[Context], List[str]]] = None,
            **kwargs: Any
    ) -> Callable[[_EventHandler], None]:
        after = after or []

        def _decorator(fn: _EventHandler) -> None:
            assert pattern not in self.handlers
            self.handlers[pattern] = Handler(fn=inject(fn), opts={"after": after, **kwargs})
        return _decorator

    def __repr__(self) -> str:
        return "{}(listener_count={})".format(self.__class__.__name__, len(self.handlers))
