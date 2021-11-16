import re
import uuid
from typing import Optional, Dict, Callable, NamedTuple, Any, Tuple, Pattern, Union, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .context import Context
    from .listener import WrappedHook


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


PARAM_REGEX = re.compile("{([a-zA-Z_][a-zA-Z0-9_]*)(:[a-zA-Z_][a-zA-Z0-9_]*)?}")


class Route:
    def __init__(
            self,
            path: str,
            fn: 'WrappedHook',
            opts: Optional[Dict[str, Any]] = None,
            parents: Union[None, List[str], Callable[['Context'], List[str]]] = None
    ):
        self.path = path
        self.path_regex, self.convertors = compile_path(path)
        self.fn = fn
        self.opts: Dict[str, Any] = opts or {}
        self.parents: Union[List[str], Callable[[Context], List[str]]] = parents or []

    def match(self, name: str) -> Tuple[bool, Dict[str, Any]]:
        match = self.path_regex.match(name)
        params = match.groupdict() if match else {}
        for k, v in params.items():
            params[k] = self.convertors[k].convert(v)
        return True if re.match(self.path_regex, name) else False, params

    def __repr__(self) -> str:
        return "{}(path={}, opts={})".format(self.__class__.__name__,
                                             self.path,
                                             self.opts)


def compile_path(path: str) -> Tuple[Pattern[str], Dict[str, Convertor]]:
    idx = 0
    path_regex = "^"
    convertors = {}
    for match in PARAM_REGEX.finditer(path):
        param_name, convertor_type = match.groups("str")
        convertor_type = convertor_type.lstrip(":")
        assert convertor_type in CONVERTOR_TYPES, f"Unknown path convertor '{convertor_type}'"
        convertor = CONVERTOR_TYPES[convertor_type]

        path_regex += re.escape(path[idx: match.start()])
        path_regex += f"(?P<{param_name}>{convertor.regex})"
        convertors[param_name] = convertor
        idx = match.end()

    path_regex += re.escape(path[idx:]) + "$"
    return re.compile(path_regex), convertors

