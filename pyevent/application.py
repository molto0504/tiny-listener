import asyncio
import signal
from typing import Optional, Dict, Callable, List, Awaitable, NamedTuple, Any, Union
from inspect import signature, Parameter
from functools import wraps

from .context import Context, Message


_EventHandler = Callable[..., Awaitable[None]]
EventHandler = Callable[[Context, Message], Awaitable[None]]


def inject(handler: _EventHandler) -> EventHandler:
    @wraps(handler)
    async def f(ctx: Context, msg: Message) -> None:
        args = []
        kwargs = {}
        for name, param in signature(handler).parameters.items():
            if param.kind == Parameter.KEYWORD_ONLY:
                kwargs[name] = None
            elif param.annotation is Context:
                args.append(ctx)
            elif param.annotation is Message:
                args.append(msg)
            else:
                args.append(None)
        return await handler(*args, **kwargs)
    return f


class Listener(NamedTuple):
    fn: EventHandler
    opts: Dict[str, Any]


class Event:
    def __init__(self, kind: str, cid: Optional[str] = None, msg: Optional[Dict] = None):
        self.kind = kind
        self.cid = cid
        self.msg = Message({"_kind_": kind, **(msg or {})})


class PyEvent:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.listeners: Dict[str, Listener] = {}
        for sig in [signal.SIGINT, signal.SIGTERM]:
            self.loop.add_signal_handler(sig, self.__exit)

        self._pre_send: List[EventHandler] = []
        self._post_send: List[EventHandler] = []
        self._error_raise: List[EventHandler] = []

    def __exit(self) -> None:
        for t in asyncio.Task.all_tasks(self.loop):
            t.cancel()

    def pre_send(self, handler: _EventHandler) -> None:
        self._pre_send.append(inject(handler))

    def post_send(self, handler: _EventHandler) -> None:
        self._post_send.append(inject(handler))

    def error_raise(self, handler: _EventHandler) -> None:
        self._error_raise.append(inject(handler))

    def send(self, event: Event) -> None:
        ctx = Context(event.cid, _app_=self)
        listener = self.listeners[event.kind]

        async def _send():
            must_done = listener.opts["must_done"]
            if isinstance(must_done, Callable):
                must_done: List[str] = must_done(ctx)
            for name in must_done:
                for job in ctx.jobs.all(name):
                    await job.wait()

            [await fn(ctx, event.msg) for fn in self._pre_send]
            try:
                await listener.fn(ctx, event.msg)
            except BaseException as e:
                if not self._error_raise:
                    raise e
                ctx.errors.append(e)
                [await fn(ctx, event.msg) for fn in self._error_raise]
            [await fn(ctx, event.msg) for fn in self._post_send]

        self.loop.create_task(_send())

    async def listen(self, send: Callable[[Event], None]):
        raise NotImplementedError()

    async def main_loop(self) -> None:
        try:
            await self.listen(self.send)
        except asyncio.CancelledError:
            pass

    def run(self) -> None:
        self.loop.run_until_complete(self.main_loop())

    def event(
            self,
            name: str,
            must_done: Union[None, List[str], Callable[[Context], List[str]]] = None,
            **kwargs: Any
    ) -> Callable[[_EventHandler], None]:
        must_done = must_done or []

        def _decorator(fn: _EventHandler) -> None:
            assert name not in self.listeners
            self.listeners[name] = Listener(fn=inject(fn), opts={"name": name, "must_done": must_done, **kwargs})
        return _decorator

    def __repr__(self) -> str:
        return "{}(listener_count={})".format(self.__class__.__name__, len(self.listeners))
