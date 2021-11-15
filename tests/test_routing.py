import uuid
from unittest import TestCase

from tiny_listener import Route


class TestRoute(TestCase):
    def setUp(self) -> None:
        async def f():
            return
        self.handler = f

    def test_ok(self):
        route = Route(path="/user/bob", fn=self.handler, parents=["/user/{name}"], opts={"foo": "bar"})
        self.assertEqual("/user/bob", route.path)
        self.assertEqual({}, route.convertors)
        self.assertEqual({"foo": "bar"}, route.opts)
        self.assertEqual((True, {}), route.match("/user/bob"))
        self.assertEqual((False, {}), route.match("/user"))
        self.assertEqual(["/user/{name}"], route.parents)

    def test_convertor_str(self):
        route = Route(path="/user/{name}", fn=self.handler)
        self.assertEqual((True, {"name": "bob"}), route.match("/user/bob"))
        self.assertEqual((False, {}), route.match("/user"))

        route = Route(path="/user/{name:str}", fn=self.handler)
        self.assertEqual((True, {"name": "bob"}), route.match("/user/bob"))
        self.assertEqual((False, {}), route.match("/user"))

    def test_convertor_int(self):
        route = Route(path="/user/{age:int}", fn=self.handler)
        self.assertEqual((True, {"age": 18}), route.match("/user/18"))
        self.assertEqual((False, {}), route.match("/user"))

    def test_convertor_float(self):
        route = Route(path="/user/{score:float}", fn=self.handler)
        self.assertEqual((True, {"score": 1.1}), route.match("/user/1.1"))
        self.assertEqual((False, {}), route.match("/user"))

    def test_convertor_path(self):
        route = Route(path="/user/{file:path}", fn=self.handler)
        self.assertEqual((True, {"file": "document/repo/foo.py"}), route.match("/user/document/repo/foo.py"))
        self.assertEqual((True, {"file": "http://localhost/home"}), route.match("/user/http://localhost/home"))
        self.assertEqual((False, {}), route.match("/user"))

    def test_convertor_uuid(self):
        route = Route(path="/user/{id:uuid}", fn=self.handler)
        self.assertEqual((True, {"id": uuid.UUID("18baadd0-9225-4cc0-a13b-69098168689f")}), route.match("/user/18baadd0-9225-4cc0-a13b-69098168689f"))
        self.assertEqual((False, {}), route.match("/user"))

    def test_convertor_complex(self):
        route = Route(path="/user/{id:uuid}/{name}/{file:path}/{age:int}/{score:float}", fn=self.handler)
        self.assertEqual((True, {
            "id": uuid.UUID("18baadd0-9225-4cc0-a13b-69098168689f"),
            "name": "bob",
            "file": "document/repo/foo.py",
            "age": 18,
            "score": 1.1
        }), route.match("/user/18baadd0-9225-4cc0-a13b-69098168689f/bob/document/repo/foo.py/18/1.1"))

    def test_convertor_not_exist(self):
        self.assertRaises(AssertionError, Route, path="/user/{name:int128}", fn=self.handler)
