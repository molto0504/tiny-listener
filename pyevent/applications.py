import re
import asyncio
import signal
from collections import namedtuple
from typing import Optional, Dict, Callable, Generator, Any, List, Union


class PyEventError(Exception):
    pass


class __UniqueCTX(type):
    ctxs: Dict[str, 'Context'] = {}

    def __call__(cls, req_id: Optional[str], **scope) -> 'Context':
        if req_id is None:
            return super().__call__(req_id, **scope)
        if req_id not in cls.ctxs:
            cls.ctxs[req_id] = super().__call__(req_id, **scope)
        ctx = cls.ctxs[req_id]
        ctx.scope.update(scope)
        return ctx


class Job:
    def __init__(self, name: str) -> None:
        self.name = name
        self.trigger = asyncio.Event()

    @property
    def is_done(self) -> bool:
        return self.trigger.is_set()

    def done(self) -> None:
        self.trigger.set()

    async def wait(self) -> Any:
        return await self.trigger.wait()

    def __repr__(self) -> str:
        return "{}(name={}, done={})".format(self.__class__.__name__, self.name, self.is_done)


class Jobs:
    def __init__(self, *names: str) -> None:
        self._jobs: Dict[str, Job] = {}
        self.add(*names)

    def add(self, *names: str) -> None:
        for name in names:
            self._jobs[name] = Job(name)

    def __match(self, pattern: str) -> Generator[Job, None, None]:
        for job in self._jobs.values():
            if re.match(pattern, job.name):
                yield job

    def first(self, pattern: str = ".*") -> Job:
        for job in self.__match(pattern):
            if not job.is_done:
                return job

    def all(self, pattern: str = ".*") -> List[Job]:
        return [job for job in self.__match(pattern) if not job.is_done]

    def get(self, name: str) -> Job:
        if name not in self._jobs:
            raise PyEventError(f"job `{name}` does not exist")
        return self._jobs[name]

    def done(self, pattern: str = ".*") -> None:
        for job in self.__match(pattern):
            job.done()

    def is_done(self, pattern: str = ".*") -> bool:
        return all(job.is_done for job in self.__match(pattern))


class Context(metaclass=__UniqueCTX):
    def __init__(self, req_id: Optional[str], **scope) -> None:
        self.req_id = req_id
        self.scope = scope
        self.jobs = Jobs()

    @property
    def app(self) -> 'PyEvent':
        return self.scope["app"]

    @classmethod
    def exist(cls, req_id: str):
        return req_id in cls.ctxs

    @classmethod
    def drop(cls, req_id) -> 'Context':
        return cls.ctxs.pop(req_id)

    def __call__(self, **scope):
        return self.scope.update(scope) or self


Listener = namedtuple("Listener", ["fn", "opts"])


class PyEvent:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.listeners: Dict[str, Listener] = {}
        for sig in [signal.SIGINT, signal.SIGTERM]:
            self.loop.add_signal_handler(sig, self.__exit)

    def __exit(self) -> None:
        for t in asyncio.Task.all_tasks(self.loop):
            t.cancel()

    async def pre_send(self, ctx: Context, message: Optional[Dict], **kwargs) -> None:
        pass

    async def post_send(self, ctx: Context, message: Optional[Dict], **kwargs) -> None:
        pass

    async def error_handler(self, ctx: Context, message, exc: BaseException) -> None:
        raise exc

    def send(
            self,
            kind: str,
            ctx: Context,
            message: Optional[Dict] = None,
            **kwargs
    ) -> None:

        async def _send():
            listener = self.listeners[kind]
            must_done = listener.opts["must_done"]

            if isinstance(must_done, Callable):
                must_done: List[str] = must_done(ctx)
            for name in must_done:
                for job in ctx.jobs.all(name):
                    await job.wait()

            await self.pre_send(ctx, message, **kwargs)
            try:
                await listener.fn(ctx(app=self), message or {})
            except BaseException as e:
                await self.error_handler(ctx, message, e)
            await self.post_send(ctx, message, **kwargs)

        self.loop.create_task(_send())

    async def __call__(self, send: Callable):
        raise NotImplementedError()

    async def main_loop(self):
        try:
            await self(self.send)
        except asyncio.CancelledError:
            pass

    def run(self):
        self.loop.run_until_complete(self.main_loop())

    def listen(self, name, must_done: Union[None, List[str], Callable] = None, **kwargs) -> Callable:
        must_done = must_done or []

        def _decorator(fn):
            assert name not in self.listeners
            self.listeners[name] = Listener(fn=fn, opts={"name": name, "must_done": must_done, **kwargs})
        return _decorator
