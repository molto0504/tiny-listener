import re
import weakref
from typing import Dict, Optional, Any, List, Coroutine, TYPE_CHECKING

from .dependant import Cache
from .event import Event


if TYPE_CHECKING:
    from .listener import Listener
    from .routing import Route


class Context:
    def __init__(self, listener: 'Listener', cid: str = "__main__", scope: Optional[Dict] = None) -> None:
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
            data: Optional[Dict] = None,
    ) -> 'Event':
        event = Event(name=name, ctx=self, route=route, timeout=timeout, data=data or {})
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

    def __repr__(self) -> str:
        return "{}(cid={}, events_count={}, scope={})".format(self.__class__.__name__,
                                                              self.cid,
                                                              len(self.events),
                                                              self.scope)
