import re
import weakref
from typing import Any, Coroutine, Dict, List, Optional, TYPE_CHECKING

from .event import Event

if TYPE_CHECKING:
    from .hook import Depends
    from .listener import Listener
    from .routing import Route

Scope = Dict[str, Any]


class Context:
    def __init__(self,
                 listener: 'Listener',
                 cid: str = "__global__",
                 scope: Optional[Scope] = None) -> None:
        self.cid = cid
        self.cache: Dict[Depends, Any] = {}
        self.scope: Scope = scope or {}
        self.events: Dict[str, Event] = {}
        self.__listener = weakref.ref(listener)

    @property
    def listener(self) -> 'Listener':
        return self.__listener()

    @property
    def is_alive(self) -> bool:
        return self.cid in self.listener.ctxs

    def drop(self) -> bool:
        if self.is_alive:
            del self.listener.ctxs[self.cid]
            return True
        return False

    def add_event(self, event: Event) -> None:
        self.events[event.name] = event

    def new_event(self,
                  name: str,
                  route: Optional['Route'] = None,
                  timeout: Optional[float] = None,
                  data: Optional[Dict] = None,
                  params: Optional[Dict[str, Any]] = None) -> 'Event':
        event = Event(name=name,
                      ctx=self,
                      route=route,
                      timeout=timeout,
                      data=data or {},
                      params=params or {})
        self.add_event(event)
        return event

    def get_events(self, pat: str = ".*") -> List[Event]:
        return [
            event
            for name, event in self.events.items()
            if re.match(pat, name)
        ]

    def fire(self,
             name: str,
             timeout: Optional[float] = None,
             data: Optional[Dict] = None) -> Coroutine or None:
        return self.listener.fire(name=name,
                                  cid=self.cid,
                                  timeout=timeout,
                                  data=data)

    def __repr__(self) -> str:
        return "{}(cid={}, scope={})".format(self.__class__.__name__,
                                             self.cid,
                                             self.scope)
