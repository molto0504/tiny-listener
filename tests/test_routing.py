import uuid
from typing import Awaitable, Callable

import pytest

from tiny_listener.routing import CONVERTOR_TYPES, Route, RouteError, compile_path


@pytest.fixture
def handler() -> Callable[..., Awaitable[None]]:
    async def mock_handler() -> None:
        return

    return mock_handler


def test_route(handler):
    route = Route(
        path="/user/bob",
        fn=handler,
        opts={"foo": "bar"},
    )
    assert route.convertors == {}
    assert route.opts == {"foo": "bar"}
    assert route.match("/user/bob") == {}
    assert route.match("/user") is None


@pytest.mark.parametrize("name", ["/user/{name}", "/user/{name:str}"])
def test_convertor_str(handler, name):
    route = Route(path=name, fn=handler)
    assert route.match("/user/bob") == {"name": "bob"}
    assert route.match("/user") is None


def test_convertor_int(handler):
    route = Route(path="/user/{age:int}", fn=handler)
    assert route.match("/user/18") == {"age": 18}
    assert route.match("/user") is None


def test_convertor_float(handler):
    route = Route(path="/user/{score:float}", fn=handler)
    assert route.match("/user/1.1") == {"score": 1.1}
    assert route.match("/user") is None


def test_convertor_path(handler):
    route = Route(path="/user/{file:path}", fn=handler)
    assert route.match("/user/document/repo/foo.py") == {"file": "document/repo/foo.py"}
    assert route.match("/user/http://localhost/home") == {"file": "http://localhost/home"}
    assert route.match("/user") is None


def test_convertor_uuid(handler):
    route = Route(path="/user/{id:uuid}", fn=handler)
    assert route.match("/user/18baadd0-9225-4cc0-a13b-69098168689f") == {
        "id": uuid.UUID("18baadd0-9225-4cc0-a13b-69098168689f")
    }
    assert route.match("/user") is None


def test_convertor_complex(handler):
    route = Route(
        path="/user/{id:uuid}/{name}/{file:path}/{age:int}/{score:float}",
        fn=handler,
    )
    assert route.match("/user/18baadd0-9225-4cc0-a13b-69098168689f/bob/document/repo/foo.py/18/1.1") == {
        "id": uuid.UUID("18baadd0-9225-4cc0-a13b-69098168689f"),
        "name": "bob",
        "file": "document/repo/foo.py",
        "age": 18,
        "score": 1.1,
    }


def test_convertor_not_exist(handler):
    with pytest.raises(RouteError):
        Route(fn=handler, path="/user/{name:int128}")


def test_compile_path():
    reg, convertors = compile_path("/user")
    assert convertors == {}

    _, convertors = compile_path("/user/{age:int}")
    assert "age" in convertors
    assert convertors["age"] is CONVERTOR_TYPES["int"]
