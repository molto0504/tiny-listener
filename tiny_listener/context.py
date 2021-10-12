import re
import weakref
import asyncio
from typing import Dict, Optional, Any, List, Set, TYPE_CHECKING
from itertools import chain


if TYPE_CHECKING:
    from .listener import Listener


class Event:
    def __init__(self, name: str, ctx: 'Context') -> None:
        self._ctx = weakref.ref(ctx)
        self.name = name
        self.detail: Dict[str, Any] = {}
        self.parents: Set[Event] = set()
        self.trigger = asyncio.Event()

    @property
    def ctx(self) -> 'Context':
        return self._ctx()

    def with_parent(self, *patterns: str) -> 'Event':
        self.parents.update(chain(*(self.ctx.get_events(pat) for pat in patterns)))
        return self

    def with_detail(self, **detail: Any) -> 'Event':
        self.detail.update(detail)
        return self

    async def __aenter__(self):
        for event in self.parents:
            await event.wait()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.done()

    @property
    def is_done(self) -> bool:
        return self.trigger.is_set()

    def done(self) -> None:
        self.trigger.set()

    async def wait(self) -> Any:
        return await self.trigger.wait()


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
        self.scope: Dict[str, Any] = scope
        self.errors: List[BaseException] = []
        if self.listener:  # TODO init by `after` arg
            self.events: Dict[str, Event] = {t: Event(t, self) for t in self.listener.__todos__}
        else:
            self.events: Dict[str, Event] = {}

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
