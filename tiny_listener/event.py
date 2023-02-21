import asyncio
import weakref
from itertools import chain
from typing import TYPE_CHECKING, Any, Callable, Dict, Generic, Set, TypeVar, Union

if TYPE_CHECKING:
    from .context import Context  # noqa # pylint: disable=unused-import
    from .listener import Listener
    from .routing import Route


CTXType = TypeVar("CTXType", bound="Context")


class Event(Generic[CTXType]):
    def __init__(
        self,
        name: str,
        ctx: CTXType,
        route: "Route",
        timeout: Union[float, None] = None,
        data: Union[Dict, None] = None,
        params: Union[Dict, None] = None,
    ) -> None:
        self.name = name
        self.timeout: Union[float, None] = timeout
        self.data = data or {}
        self.params: Dict[str, Any] = params or {}
        self.error: Union[BaseException, None] = None
        self.__route = route
        self.__ctx: Callable[..., CTXType] = weakref.ref(ctx)  # type: ignore
        self.__done = asyncio.Event()
        self.__result: Any = None
        self.__prevent_done: bool = False

    @property
    def prevent_done(self) -> bool:
        return self.__prevent_done

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
    def after(self) -> Set["Event"]:
        return set(chain(*(self.ctx.get_events(pat) for pat in self.route.after)))

    @property
    def result(self) -> Any:
        return self.__result

    @property
    def is_done(self) -> bool:
        return self.__done.is_set()

    def not_done_yet(self) -> None:
        self.__prevent_done = True

    def done(self) -> None:
        self.__done.set()

    async def wait_until_done(self, timeout: Union[float, None] = None) -> None:
        """
        :raises: asyncio.TimeoutError
        """
        await asyncio.wait_for(self.__done.wait(), timeout)

    async def __call__(self, executor: Any = None) -> Any:
        self.__result = await self.route.hook(self, executor)
        return self.__result

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.route.path}, route={self.name}, params={self.params}, data={self.data})"
