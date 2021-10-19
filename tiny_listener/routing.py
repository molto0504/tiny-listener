import re
import uuid
from typing import Optional, Dict, Callable, Awaitable, NamedTuple, Any, Tuple, Pattern
from inspect import signature, Parameter
from functools import wraps

from .context import Context, Event


class RoutingError(BaseException):
    pass


class Convertor(NamedTuple):
    regex: str
    convert: Callable[[Any], Any]


CONVERTOR_TYPES: Dict[str, Convertor] = {
    "str": Convertor("[^/]+", lambda s: str(s)),
    "int": Convertor("[0-9]+", lambda s: int(s)),
    "float": Convertor("[0-9]+(.[0-9]+)?", lambda s: float(s)),
    "path": Convertor(".*", lambda s: str(s)),
    "uuid": Convertor("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", lambda x: uuid.UUID(x))
}


class Params(dict):
    pass


_EventHandler = Callable[..., Awaitable[None]]
EventHandler = Callable[[Context, Event, Params], Awaitable[None]]


def as_handler(handler: _EventHandler) -> EventHandler:
    @wraps(handler)
    async def f(ctx: Context, event: Event, params: Params) -> None:
        args = []
        kwargs = {}
        for name, param in signature(handler).parameters.items():
            if param.kind == Parameter.KEYWORD_ONLY:
                kwargs[name] = None
            elif param.annotation is Context:
                args.append(ctx)
            elif param.annotation is Event:
                args.append(event)
            elif param.annotation is Params:
                args.append(params)
            else:
                args.append(None)
        return await handler(*args, **kwargs)
    return f


class Route:
    PARAM_REGEX = re.compile("{([a-zA-Z_][a-zA-Z0-9_]*)(:[a-zA-Z_][a-zA-Z0-9_]*)?}")

    def __init__(self, path: str, fn: _EventHandler, opts: Optional[Dict[str, Any]] = None):
        self.path = path
        self.path_regex, self.convertors = self.compile_path()
        self.fn = as_handler(fn)
        self.opts: Dict[str, Any] = opts or {}

    def match(self, name: str) -> Tuple[bool, Dict[str, Any]]:
        match = self.path_regex.match(name)
        params = match.groupdict() if match else {}
        for k, v in params.items():
            params[k] = self.convertors[k].convert(v)
        return True if re.match(self.path_regex, name) else False, params

    def compile_path(self) -> Tuple[Pattern[str], Dict[str, Convertor]]:
        idx = 0
        path_regex = "^"
        convertors = {}
        for match in self.PARAM_REGEX.finditer(self.path):
            param_name, convertor_type = match.groups("str")
            convertor_type = convertor_type.lstrip(":")
            if convertor_type not in CONVERTOR_TYPES:
                raise RoutingError(f"Unknown path convertor '{convertor_type}'")
            convertor = CONVERTOR_TYPES[convertor_type]

            path_regex += re.escape(self.path[idx: match.start()])
            path_regex += f"(?P<{param_name}>{convertor.regex})"

            convertors[param_name] = convertor

            idx = match.end()

        path_regex += re.escape(self.path[idx:]) + "$"
        return re.compile(path_regex), convertors
