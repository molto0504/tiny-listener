import asyncio
import weakref
from collections import defaultdict
from typing import TYPE_CHECKING, Any, DefaultDict, Dict, Final, List, Union

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
        :param listener: Listener instance
        :param cid: Context ID
        :param scope: Context scope
        """
        self.cid: Final = cid
        self.cache: Final[Dict[Depends, Any]] = {}
        self.scope: Final[Scope] = scope or {}
        self.events: Final[DefaultDict[Route, List[Event]]] = defaultdict(list)
        self.__listener: weakref.ReferenceType["Listener"] = weakref.ref(listener)

    @property
    def listener(self) -> "Listener":
        return self.__listener()  # type: ignore

    @property
    def is_alive(self) -> bool:
        return self.cid in self.listener.ctxs

    def drop(self) -> bool:
        if self.is_alive:
            del self.listener.ctxs[self.cid]
            return True
        return False

    def new_event(self, route: "Route", data: Dict[str, Any]) -> Event:
        """
        :param route: Route instance
        :param data: Event data
        :raises: EventAlreadyExists
        """
        event = Event(self, route, data=data)
        self.events[route].append(event)
        return event

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
