from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict

if TYPE_CHECKING:
    from .event import Event  # noqa # pylint: disable=unused-import

PathParams = Dict[str, Any]
CoroFunc = Callable[..., Awaitable[Any]]
HookFunc = Callable[["Event", PathParams], Awaitable[Any]]
