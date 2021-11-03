import re
import weakref
import asyncio
from typing import Dict, Optional, Any, List, Set, TYPE_CHECKING
from concurrent.futures import TimeoutError
from itertools import chain


if TYPE_CHECKING:
    from .listener import Listener
    from .routing import Route


class Event:
    def __init__(
            self,
            name: str,
            ctx: 'Context',
            route: Optional['Route'] = None,
            timeout: Optional[float] = None,
            **data
    ) -> None:
        self._ctx = weakref.ref(ctx)
        self.name = name
        self.data = data
        self.trigger = asyncio.Event()
        self.route: Optional[Route] = route
        self.timeout: Optional[float] = timeout

    @property
    def ctx(self) -> 'Context':
        return self._ctx()

    @property
    def parents(self) -> Set['Event']:
        if self.route:
            return set(chain(*(self.ctx.get_events(pat) for pat in self.route.parents)))
        return set()

    async def __aenter__(self) -> Optional[TimeoutError]:
        try:
            for event in self.parents:
                await asyncio.wait_for(event.wait(), event.timeout)
        except TimeoutError as e:
            return e

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.done()

    @property
    def is_done(self) -> bool:
        return self.trigger.is_set()

    def done(self) -> None:
        self.trigger.set()

    async def wait(self) -> Any:
        return await self.trigger.wait()

    def __repr__(self) -> str:
        return "{}(name={}, data={})".format(self.__class__.__name__,
                                             self.name,
                                             self.data)


class __UniqueCTX(type):
    ctxs: Dict[str, 'Context'] = {}

    def __call__(cls, cid: str = "_global_", **scope) -> 'Context':
        if cid not in cls.ctxs:
            cls.ctxs[cid] = super().__call__(cid, **scope)
        ctx = cls.ctxs[cid]
        ctx.scope.update(scope)
        return ctx


class Context(metaclass=__UniqueCTX):
    def __init__(self, cid: str = "_global_", **scope) -> None:
        self.cid = cid
        self.scope: Dict[str, Any] = {"__depends_cache__": {}}
        self.scope.update(scope)
        self.errors: List[BaseException] = []
        self.events: Dict[str, Event] = {}

    def new_event(
            self,
            name: str,
            route: Optional['Route'] = None,
            timeout: Optional[float] = None,
            **data
    ) -> 'Event':
        event = Event(name=name, ctx=self, route=route, timeout=timeout, **data)
        self.events[name] = event
        return event

    def get_events(self, pat: str = ".*") -> List[Event]:
        return [event for name, event in self.events.items() if re.match(pat, name)]

    @property
    def listener(self) -> Optional['Listener']:
        return self.scope.get("_listener_")

    @classmethod
    def exist(cls, cid: str) -> bool:
        return cid in cls.ctxs

    @classmethod
    def drop(cls, cid) -> 'Context':
        return cls.ctxs.pop(cid)

    def __call__(self, **scope) -> 'Context':
        return self.scope.update(scope) or self

    def __repr__(self) -> str:
        return "{}(cid={}, scope={}, errors={})".format(self.__class__.__name__,
                                                        self.cid,
                                                        self.scope,
                                                        self.errors)
