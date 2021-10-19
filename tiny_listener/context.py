import re
import weakref
import asyncio
from typing import Dict, Optional, Any, List, Set, TYPE_CHECKING
from concurrent.futures import TimeoutError
from itertools import chain


if TYPE_CHECKING:
    from .listener import Listener


class Event:
    def __init__(self, name: str, ctx: 'Context') -> None:
        self._ctx = weakref.ref(ctx)
        self.name = name
        self.data = dict()
        self.trigger = asyncio.Event()

        self.parents_pat: Set[str] = set()
        self.parents: Set[Event] = set()
        self.parents_count: Optional[int] = None
        self.parents_ready = asyncio.Event()
        self.parents_timeout: Optional[float] = None

    @property
    def ctx(self) -> 'Context':
        return self._ctx()

    def load_parents(self):
        self.parents = set(chain(*(self.ctx.get_events(pat) for pat in self.parents_pat)))
        if self.parents_count is not None and len(self.parents) == self.parents_count:
            self.parents_ready.set()

    def add_parents(self, *parents_pat: str) -> 'Event':
        self.parents_pat.update(set(parents_pat))
        self.load_parents()
        return self

    def set_data(self, data: Dict) -> 'Event':
        self.data.update(data)
        return self

    async def __aenter__(self) -> Optional[TimeoutError]:
        try:
            if self.parents_count is not None:
                await asyncio.wait_for(self.parents_ready.wait(), self.parents_timeout)
            for event in self.parents:
                await asyncio.wait_for(event.wait(), self.parents_timeout)
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

    def new_event(self, name: str) -> 'Event':
        event = Event(name, self)
        self.events[name] = event
        event.load_parents()
        [i.load_parents() for i in self.events.values()]
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
