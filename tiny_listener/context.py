"""

           Listener([ctxs, routes], add_ctx, add_route)
              |                         |
      |---------------|           |-----------|
   context          context     route        route
      |
   |-----|
event   event(match_a_route)
   |     |
route   route


"""
import re
import weakref
import asyncio
from typing import Dict, Optional, Any, List, Set, Coroutine, Callable, TYPE_CHECKING
from itertools import chain


if TYPE_CHECKING:
    from .listener import Listener
    from .routing import Route
from .dependant import Cache


class EventError(BaseException):
    pass


class EventManager:
    def __aenter__(self):
        pass

    def __anext__(self):
        pass


class Event:
    def __init__(
            self,
            name: str,
            ctx: 'Context',
            route: Optional['Route'] = None,
            timeout: Optional[float] = None,
            data: Optional[Dict] = None
    ) -> None:
        self._ctx = weakref.ref(ctx)
        self.name = name
        self.data = data
        self.trigger = asyncio.Event()
        self.route: Optional[Route] = route
        self.timeout: Optional[float] = timeout
        self._error: Optional[EventError] = None

    @property
    def ctx(self) -> 'Context':
        return self._ctx()

    @property
    def parents(self) -> Set['Event']:
        if self.route:
            return set(chain(*(self.ctx.get_events(pat) for pat in self.route.parents)))
        return set()

    def next(self):
        self._error = None

    async def __aenter__(self) -> Optional[EventError]:
        for event in self.parents:
            await asyncio.wait_for(event.wait(), None)
            if event._error:
                return event._error

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


# class __UniqueCTX(type):
#     ctxs: Dict[str, 'Context'] = {}
#
#     def __call__(cls, cid: str = "_global_", **scope) -> 'Context':
#         if cid not in cls.ctxs:
#             cls.ctxs[cid] = super().__call__(cid, **scope)
#         ctx = cls.ctxs[cid]
#         ctx.scope.update(scope)
#         return ctx


class ContextError(BaseException):
    pass


class Context:
    def __init__(self, listener: Listener, cid: str = "__main__", scope: Optional[Dict] = None) -> None:
        self.cid = cid
        self.cache: Cache = Cache()
        self.__listener = weakref.ref(listener)
        self.scope: Dict[str, Any] = scope or {}
        self.events: Dict[str, Event] = {}

    @property
    def listener(self) -> 'Listener':
        return self.__listener()

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

    def fire(
            self,
            name: str,
            timeout: Optional[float] = None,
            data: Optional[Dict] = None
    ) -> Coroutine or None:
        return self.listener.fire(name=name, cid=self.cid, timeout=timeout, data=data)

    @classmethod
    def exist(cls, cid: str) -> bool:
        return cid in cls.ctxs

    @classmethod
    def drop(cls, cid) -> 'Context':
        return cls.ctxs.pop(cid)

    def __call__(self, **scope) -> 'Context':
        return self.scope.update(scope) or self

    def __repr__(self) -> str:
        return "{}(cid={}, scope={})".format(self.__class__.__name__,
                                             self.cid,
                                             self.scope)
