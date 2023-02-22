import asyncio
import re
import warnings
import weakref
from typing import TYPE_CHECKING, Any, Callable, Dict, List, TypeVar, Union

from .event import Event

if TYPE_CHECKING:
    from .hook import Depends
    from .listener import Listener  # noqa # pylint: disable=unused-import
    from .routing import Route

Scope = Dict[str, Any]


class EventAlreadyExist(Exception):
    pass


ListenerType = TypeVar("ListenerType", bound="Listener")


class Context:
    def __init__(
        self,
        listener: ListenerType,
        cid: str,
        scope: Union[Scope, None] = None,
    ) -> None:
        """
        :param listener: Listener instance
        :param cid: Context ID
        :param scope: Context scope
        """
        self.cid = cid
        self.cache: Dict[Depends, Any] = {}
        self.scope: Scope = scope or {}
        self.events: Dict[str, Event] = {}
        self.__listener: Callable[..., ListenerType] = weakref.ref(listener)  # type: ignore

    @property
    def listener(self) -> ListenerType:
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
        :raises: EventAlreadyExist
        """
        if name in self.events:
            raise EventAlreadyExist(f"Event `{name}` already exist in context `{self}`")
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

    def fire(
        self, name: str, timeout: Union[float, None] = None, data: Union[Dict, None] = None
    ) -> asyncio.Task:  # pragma: no cover
        warnings.warn("`fire` is deprecated since ver0.0.13, use trigger_event instead", DeprecationWarning)
        return self.trigger_event(name, timeout, data)

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
