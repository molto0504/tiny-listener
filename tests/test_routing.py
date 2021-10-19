import re
from unittest import TestCase

from tiny_listener import Context, inject, Listener, Event, Route, Path, RoutingError


class TestInject(TestCase):
    def setUp(self) -> None:
        class App(Listener):
            def listen(self, _): ...

        self.app = App()
        self.ctx = Context("ctx_inject", _listener_=self.app)
        self.event = self.ctx.new_event("foo")
        self.path = Path({"key": "val"})

    def test_inject_ok(self):
        @inject
        async def foo(ctx: Context):
            assert ctx is self.ctx
        self.app.loop.run_until_complete(foo(self.ctx, self.event, self.path))

        @inject
        async def foo(arg_1, ctx: Context, arg_2):
            assert arg_1 is arg_2 is None
            assert ctx is self.ctx
        self.app.loop.run_until_complete(foo(self.ctx, self.event, self.path))

        @inject
        async def foo(arg_1, ctx: Context, *, arg_2=None):
            assert arg_1 is arg_2 is None
            assert ctx is self.ctx
        self.app.loop.run_until_complete(foo(self.ctx, self.event, self.path))

        @inject
        async def foo(*, ctx: Context):
            assert ctx is None
        self.app.loop.run_until_complete(foo(self.ctx, self.event, self.path))

        @inject
        async def foo(ctx_1: Context, *, ctx_2: Context):
            assert ctx_1 is self.ctx
            assert ctx_2 is None
        self.app.loop.run_until_complete(foo(self.ctx, self.event, self.path))

    def test_inject_all(self):
        @inject
        async def foo(ctx: Context, event: Event, params: Path):
            assert ctx is self.ctx
            assert event is self.event
            assert params == {"key": "val"}
        self.app.loop.run_until_complete(foo(self.ctx, self.event, self.path))

        @inject
        async def foo(arg_1, ctx: Context, arg_2, event: Event, params: Path):
            assert arg_1 is arg_2 is None
            assert ctx is self.ctx
            assert event is self.event
            assert params == {"key": "val"}
        self.app.loop.run_until_complete(foo(self.ctx, self.event, self.path))

        @inject
        async def foo(ctx: Context, *, event: Event, params: Path):
            assert ctx is self.ctx
            assert event is None
            assert params is None
        self.app.loop.run_until_complete(foo(self.ctx, self.event, self.path))


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

    def test_convertor_not_exist(self):
        self.assertRaises(RoutingError, Route, path="/user/{name:int128}", fn=self.handler)
