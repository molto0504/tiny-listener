import asyncio
import weakref
from itertools import chain
from typing import Any, Dict, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from .listener import Listener
    from .context import Context
    from .routing import Route


class Event:
    def __init__(self,
                 name: str,
                 ctx: 'Context',
                 route: Optional['Route'],
                 timeout: Optional[float] = None,
                 data: Optional[Dict] = None) -> None:
        self.name = name
        self.timeout: Optional[float] = timeout
        self.data = data or {}
        self.params: Dict[str, Any] = {}
        self.error: Optional[BaseException] = None
        self.__route = route
        self.__ctx = weakref.ref(ctx)
        self.__done = asyncio.Event()

    @property
    def route(self) -> 'Route':
        return self.__route

    @property
    def ctx(self) -> 'Context':
        return self.__ctx()

    @property
    def listener(self) -> 'Listener':
        return self.ctx.listener

    @property
    def parents(self) -> Set['Event']:
        return set(chain(*(self.ctx.get_events(pat) for pat in self.route.parents)))

    @property
    def is_done(self) -> bool:
        return self.__done.is_set()

    def done(self) -> None:
        self.__done.set()

    async def wait_until_done(self, timeout: Optional[float] = None) -> None:
        """
        :raises: asyncio.futures.TimeoutError
        """
        await asyncio.wait_for(self.__done.wait(), timeout)

    async def __call__(self, executor: Any):
        return await self.route.hook(self, executor)

    def __repr__(self) -> str:
        return "{}(name={}, route={}, data={})".format(self.__class__.__name__,
                                                       self.route.path if self.route else None,
                                                       self.name,
                                                       self.data)
