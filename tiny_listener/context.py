import asyncio
import re
import weakref
from typing import TYPE_CHECKING, Any, Dict, List, Union

from .errors import EventAlreadyExists, ListenerNotFound
from .event import Event

if TYPE_CHECKING:
    from .hook import Depends
    from .listener import Listener  # noqa # pylint: disable=unused-import
    from .routing import Route

Scope = Dict[str, Any]


class Context:
    def __init__(
        self,
        listener: "Listener",
        cid: str,
        scope: Union[Scope, None] = None,
    ) -> None:
        """
        :param cid: Context ID
        :param scope: Context scope
        """
        self.cid = cid
        self.cache: Dict[Depends, Any] = {}
        self.scope: Scope = scope or {}
        self.events: Dict[str, Event] = {}
        self.__listener: weakref.ReferenceType["Listener"] = weakref.ref(listener)

    @property
    def listener(self) -> "Listener":
        return self.__listener()  # type: ignore

    @property
    def is_alive(self) -> bool:
        try:
            return self.cid in self.listener.ctxs
        except ListenerNotFound:
            return False

    def drop(self) -> bool:
        if self.is_alive:
            del self.listener.ctxs[self.cid]
            return True
        return False

    def add_event(self, event: Event) -> None:
        """
        :param event: Event instance
        """
        self.events[event.name] = event

    def new_event(
        self,
        name: str,
        route: "Route",
        timeout: Union[float, None] = None,
        data: Union[Dict, None] = None,
        params: Union[Dict[str, Any], None] = None,
    ) -> "Event":
        """
        :param name: Event name
        :param route: Route instance
        :param timeout: Timeout
        :param data: Event data
        :param params: Event params
        :raises: EventAlreadyExists
        """
        if name in self.events:
            raise EventAlreadyExists(f"Event `{name}` already exist in context `{self}`")
        event = Event(
            name=name,
            ctx=self,
            route=route,
            timeout=timeout,
            data=data or {},
            params=params or {},
        )
        self.add_event(event)
        return event

    def get_events(self, pat: str = ".*") -> List[Event]:
        """
        :param pat: Pattern
        """
        return [event for name, event in self.events.items() if re.match(pat, name)]

    def trigger_event(
        self, name: str, timeout: Union[float, None] = None, data: Union[Dict, None] = None
    ) -> asyncio.Task:
        """
        :param name: Event name
        :param timeout: Timeout
        :param data: Event data
        """
        return self.listener.trigger_event(name=name, cid=self.cid, timeout=timeout, data=data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(cid={self.cid}, scope={self.scope})"
