from typing import TYPE_CHECKING, Any, Awaitable, Callable

if TYPE_CHECKING:
    from .event import Event  # noqa # pylint: disable=unused-import

CoroFunc = Callable[..., Awaitable[Any]]
HookFunc = Callable[["Event"], Awaitable[Any]]
