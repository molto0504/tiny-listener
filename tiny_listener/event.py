import weakref
import asyncio
from typing import Dict, Optional, Any, Set, TYPE_CHECKING
from itertools import chain

if TYPE_CHECKING:
    from .context import Context
    from .routing import Route


class Event:
    def __init__(
            self,
            name: str,
            ctx: 'Context',
            route: Optional['Route'],
            timeout: Optional[float] = None,
            data: Optional[Dict] = None
    ) -> None:
        self.name = name
        self._ctx = weakref.ref(ctx)
        self.route = route
        self.timeout: Optional[float] = timeout
        self.data = data or {}
        self.trigger = asyncio.Event()

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
        return "{}(name={}, route={}, data={})".format(self.__class__.__name__,
                                                       self.route.path if self.route else None,
                                                       self.name,
                                                       self.data)
