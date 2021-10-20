import uuid
from unittest import TestCase
from typing import Dict

from tiny_listener import Context, as_handler, Listener, Event, Route, Params, NotFound, Depends


class TestInject(TestCase):
    def setUp(self) -> None:
        class App(Listener):
            def listen(self, _): ...

        self.app = App()
        self.ctx = Context("ctx_as_handler", _listener_=self.app)
        self.event = self.ctx.new_event("foo")
        self.path = Params({"key": "val"})

    def test_as_handler_ok(self):
        @as_handler
        async def foo(ctx: Context):
            assert ctx is self.ctx
        self.app.loop.run_until_complete(foo(self.ctx, self.event, self.path))

        @as_handler
        async def foo(arg_1, ctx: Context, arg_2):
            assert arg_1 is arg_2 is None
            assert ctx is self.ctx
        self.app.loop.run_until_complete(foo(self.ctx, self.event, self.path))

        @as_handler
        async def foo(arg_1, ctx: Context, *, arg_2=None):
            assert arg_1 is arg_2 is None
            assert ctx is self.ctx
        self.app.loop.run_until_complete(foo(self.ctx, self.event, self.path))

        @as_handler
        async def foo(*, ctx: Context):
            assert ctx is None
        self.app.loop.run_until_complete(foo(self.ctx, self.event, self.path))

        @as_handler
        async def foo(ctx_1: Context, *, ctx_2: Context):
            assert ctx_1 is self.ctx
            assert ctx_2 is None
        self.app.loop.run_until_complete(foo(self.ctx, self.event, self.path))

    def test_as_handler_all(self):
        @as_handler
        async def foo(ctx: Context, event: Event, params: Params):
            assert ctx is self.ctx
            assert event is self.event
            assert params == {"key": "val"}
        self.app.loop.run_until_complete(foo(self.ctx, self.event, self.path))

        @as_handler
        async def foo(arg_1, ctx: Context, arg_2, event: Event, params: Params):
            assert arg_1 is arg_2 is None
            assert ctx is self.ctx
            assert event is self.event
            assert params == {"key": "val"}
        self.app.loop.run_until_complete(foo(self.ctx, self.event, self.path))

        @as_handler
        async def foo(ctx: Context, *, event: Event, params: Params):
            assert ctx is self.ctx
            assert event is None
            assert params is None
        self.app.loop.run_until_complete(foo(self.ctx, self.event, self.path))

    def test_as_handler_depends(self):
        async def get_params(params: Params):
            return params

        async def get_info(ctx: Context, *, data: Dict = Depends(get_params)):
            return f"{ctx.cid}:{data['key']}"

        @as_handler
        async def foo(ctx: Context, *, info=Depends(get_info)):
            assert ctx is self.ctx
            assert info == "ctx_as_handler:val"
        self.app.loop.run_until_complete(foo(self.ctx, self.event, self.path))

    def test_as_handler_depends_use_cache(self):
        times = 0

        async def dep():
            nonlocal times
            times += 1
            return ...

        @as_handler
        async def foo(ctx: Context, *, foo=Depends(dep), bar=Depends(dep)):
            assert ctx is self.ctx
            assert foo is ...
            assert bar is ...
        self.app.loop.run_until_complete(foo(self.ctx, self.event, self.path))
        self.assertEqual(1, times)


class TestRoute(TestCase):
    def setUp(self) -> None:
        async def f():
            return
        self.handler = f

    def test_ok(self):
        route = Route(path="/user/bob", fn=self.handler, opts={"foo": "bar"})
        self.assertEqual("/user/bob", route.path)
        self.assertEqual({}, route.convertors)
        self.assertEqual({"foo": "bar"}, route.opts)
        self.assertEqual((True, {}), route.match("/user/bob"))
        self.assertEqual((False, {}), route.match("/user"))

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
