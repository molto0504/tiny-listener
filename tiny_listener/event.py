import asyncio
import weakref
from typing import TYPE_CHECKING, Any, Callable, Dict, Generic, List, TypeVar, Union

if TYPE_CHECKING:
    from .context import Context  # noqa # pylint: disable=unused-import
    from .listener import Listener
    from .routing import Route


CTXType = TypeVar("CTXType", bound="Context")


class Event(Generic[CTXType]):
    def __init__(
        self,
        ctx: CTXType,
        route: "Route",
        timeout: Union[float, None] = None,
        data: Union[Dict, None] = None,
    ) -> None:
        self.timeout: Union[float, None] = timeout
        self.data = data or {}
        self.params: Dict[str, Any] = {}
        self.error: Union[Exception, None] = None
        self.__route = route
        self.__ctx: Callable[..., CTXType] = weakref.ref(ctx)  # type: ignore
        self.__done = asyncio.Event()
        self.__auto_done: bool = True
        self.__result: Any = None
        self.running: bool = False

    @property
    def result(self) -> Any:
        return self.__result

    @property
    def auto_done(self) -> bool:
        return self.__auto_done

    @property
    def route(self) -> "Route":
        return self.__route

    @property
    def ctx(self) -> "CTXType":
        return self.__ctx()

    @property
    def listener(self) -> "Listener":
        return self.ctx.listener

    @property
    def is_done(self) -> bool:
        return self.__done.is_set()

    def prevent_auto_done(self) -> None:
        self.__auto_done = False

    def done(self) -> None:
        self.__done.set()

    async def wait_until_done(self) -> None:
        """
        :raises: asyncio.TimeoutError
        """
        await self.__done.wait()

    async def wait_event_done(self, event_name: str, n: int = 1, timeout: Union[float, None] = None) -> List[Any]:
        route = self.listener.get_route(event_name)

        async def _wait() -> List[Any]:
            events = self.ctx.events[route]
            while len(events) != n:
                await asyncio.sleep(0.5)
            for event in events:
                await event.wait_until_done()
            return [event.result for event in events]

        return await asyncio.wait_for(_wait(), timeout=timeout)

    async def __call__(self) -> Any:
        """
        :raises: asyncio.TimeoutError
        """
        self.__result = await self.route.hook(self)
        return self.__result

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.route.path}, route={self.route}, params={self.params}, data={self.data})"
