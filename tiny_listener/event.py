import weakref
import asyncio
from typing import Dict, Optional, Any, List, Set, Coroutine, Callable, TYPE_CHECKING
from itertools import chain

if TYPE_CHECKING:
    from .context import Context
    from .routing import Route


class Event:
    def __init__(
            self,
            name: str,
            ctx: 'Context',
            route: 'Route' = None,
            timeout: Optional[float] = None,
            data: Optional[Dict] = None
    ) -> None:
        self._ctx = weakref.ref(ctx)
        self.name = name
        self.data = data or {}
        self.trigger = asyncio.Event()
        self.route: Route = route
        self.timeout: Optional[float] = timeout

    @property
    def ctx(self) -> 'Context':
        return self._ctx()

    @property
    def parents(self) -> Set['Event']:
        return set(chain(*(self.ctx.get_events(pat) for pat in self.route.parents)))

    @property
    def is_done(self) -> bool:
        return self.trigger.is_set()

    def done(self) -> None:
        self.trigger.set()

    async def wait(self) -> Any:
        return await self.trigger.wait()

    def __repr__(self) -> str:
        return "{}(name={}, route={}. data={})".format(self.__class__.__name__,
                                                       self.route.path,
                                                       self.name,
                                                       self.data)
