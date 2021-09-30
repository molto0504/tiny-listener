import re
import asyncio
import signal
from collections import namedtuple
from typing import Optional, Dict, Callable, Generator, Any, List, Union
from inspect import signature, Parameter
from functools import wraps


class PyEventError(Exception):
    pass


def inject(fn) -> Callable:
    @wraps(fn)
    def f(ctx: Context, msg: Message):
        args = []
        kwargs = {}
        for name, param in signature(fn).parameters.items():
            if param.kind == Parameter.KEYWORD_ONLY:
                kwargs[name] = None
            elif param.annotation is Context:
                args.append(ctx)
            elif param.annotation is Message:
                args.append(msg)
            else:
                args.append(None)
        return fn(*args, **kwargs)
    return f


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


class __UniqueCTX(type):
    ctxs: Dict[str, 'Context'] = {}

    def __call__(cls, cid: Optional[str] = None, **scope) -> 'Context':
        if cid is None:
            return super().__call__(cid, **scope)
        if cid not in cls.ctxs:
            cls.ctxs[cid] = super().__call__(cid, **scope)
        ctx = cls.ctxs[cid]
        ctx.scope.update(scope)
        return ctx


class Context(metaclass=__UniqueCTX):
    def __init__(self, cid: Optional[str] = None, **scope) -> None:
        self.cid = cid
        self.scope: Dict[str, Any] = {"_app_": None, **scope}
        self.jobs = Jobs()
        self.errors: List[BaseException] = []

    @property
    def app(self) -> 'PyEvent':
        return self.scope["_app_"]

    @classmethod
    def exist(cls, cid: str):
        return cid in cls.ctxs

    @classmethod
    def drop(cls, cid) -> 'Context':
        return cls.ctxs.pop(cid)

    def __call__(self, **scope):
        return self.scope.update(scope) or self


class Message(Dict):
    pass


Listener = namedtuple("Listener", ["fn", "opts"])


class PyEvent:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.listeners: Dict[str, Listener] = {}
        for sig in [signal.SIGINT, signal.SIGTERM]:
            self.loop.add_signal_handler(sig, self.__exit)
        self._pre_send: List[Callable] = []
        self._post_send: List[Callable] = []
        self._error_raise: List[Callable] = []

    def __exit(self) -> None:
        for t in asyncio.Task.all_tasks(self.loop):
            t.cancel()

    def pre_send(self, fn):
        self._pre_send.append(inject(fn))

    def post_send(self, fn):
        self._post_send.append(inject(fn))

    def error_raise(self, fn):
        self._error_raise.append(inject(fn))

    def send(
            self,
            kind: str,
            cid: Optional[str] = None,
            message: Optional[Dict] = None,
    ) -> None:
        ctx = Context(cid, _app_=self)
        listener = self.listeners[kind]
        message = {"_kind_": kind, **(message or {})}

        async def _send():
            must_done = listener.opts["must_done"]
            if isinstance(must_done, Callable):
                must_done: List[str] = must_done(ctx)
            for name in must_done:
                for job in ctx.jobs.all(name):
                    await job.wait()

            [await fn(ctx, message) for fn in self._pre_send]
            try:
                await listener.fn(ctx, message)
            except BaseException as e:
                ctx.errors.append(e)
                [await fn(ctx, message) for fn in self._error_raise]
            [await fn(ctx, message) for fn in self._post_send]

        self.loop.create_task(_send())

    async def listen(self, send: Callable):
        raise NotImplementedError()

    async def main_loop(self) -> None:
        try:
            await self.listen(self.send)
        except asyncio.CancelledError:
            pass

    def run(self):
        self.loop.run_until_complete(self.main_loop())

    def event(self, name, must_done: Union[None, List[str], Callable] = None, **kwargs) -> Callable:
        must_done = must_done or []

        def _decorator(fn):
            assert name not in self.listeners
            self.listeners[name] = Listener(fn=inject(fn), opts={"name": name, "must_done": must_done, **kwargs})
        return _decorator
