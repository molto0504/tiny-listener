import uuid
from unittest import TestCase

import pytest

from tiny_listener.routing import CONVERTOR_TYPES, Route, RouteError, compile_path


def test_compile_path():
    reg, convertors = compile_path("/user")
    assert convertors == {}

    _, convertors = compile_path("/user/{age:int}")
    assert "age" in convertors
    assert convertors["age"] is CONVERTOR_TYPES["int"]


class TestRoute(TestCase):
    def setUp(self) -> None:
        async def f():
            return

        self.handler = f

    def test_ok(self):
        route = Route(path="/user/bob", fn=self.handler, after=["/user/{name}"], opts={"foo": "bar"})
        self.assertEqual("/user/bob", route.path)
        self.assertEqual({}, route.convertors)
        self.assertEqual({"foo": "bar"}, route.opts)
        self.assertEqual({}, route.match("/user/bob"))
        self.assertIsNone(route.match("/user"))
        self.assertEqual(["/user/{name}"], route.after)

    def test_convertor_str(self):
        route = Route(path="/user/{name}", fn=self.handler)
        self.assertEqual({"name": "bob"}, route.match("/user/bob"))
        self.assertIsNone(route.match("/user"))

        route = Route(path="/user/{name:str}", fn=self.handler)
        self.assertEqual({"name": "bob"}, route.match("/user/bob"))
        self.assertIsNone(route.match("/user"))

    def test_convertor_int(self):
        route = Route(path="/user/{age:int}", fn=self.handler)
        self.assertEqual({"age": 18}, route.match("/user/18"))
        self.assertIsNone(route.match("/user"))

    def test_convertor_float(self):
        route = Route(path="/user/{score:float}", fn=self.handler)
        self.assertEqual({"score": 1.1}, route.match("/user/1.1"))
        self.assertIsNone(route.match("/user"))

    def test_convertor_path(self):
        route = Route(path="/user/{file:path}", fn=self.handler)
        self.assertEqual({"file": "document/repo/foo.py"}, route.match("/user/document/repo/foo.py"))
        self.assertEqual({"file": "http://localhost/home"}, route.match("/user/http://localhost/home"))
        self.assertIsNone(route.match("/user"))

    def test_convertor_uuid(self):
        route = Route(path="/user/{id:uuid}", fn=self.handler)
        self.assertEqual({"id": uuid.UUID("18baadd0-9225-4cc0-a13b-69098168689f")}, route.match("/user/18baadd0-9225-4cc0-a13b-69098168689f"))
        self.assertIsNone(route.match("/user"))

    def test_convertor_complex(self):
        route = Route(path="/user/{id:uuid}/{name}/{file:path}/{age:int}/{score:float}", fn=self.handler)
        self.assertEqual(route.match("/user/18baadd0-9225-4cc0-a13b-69098168689f/bob/document/repo/foo.py/18/1.1"),
                         {
                             "id": uuid.UUID("18baadd0-9225-4cc0-a13b-69098168689f"),
                             "name": "bob",
                             "file": "document/repo/foo.py",
                             "age": 18,
                             "score": 1.1
                         })

    def test_convertor_not_exist(self):
        with pytest.raises(RouteError):
            Route(path="/user/{name:int128}", fn=self.handler)
