from unittest import TestCase
from typing import Callable

from tiny_listener import Context, inject, Listener, Event


class TestInject(TestCase):
    def setUp(self) -> None:
        class App(Listener):
            __todos__ = ["foo"]

        self.app = App()
        self.ctx = Context("ctx_inject", _listener_=self.app)
        self.event = self.ctx.events["foo"]

    def test_inject(self):
        @inject
        async def foo(ctx: Context):
            assert ctx is self.ctx
        self.app.loop.run_until_complete(foo(self.ctx, self.event))

        @inject
        async def foo(arg_1, ctx: Context, arg_2):
            assert arg_1 is arg_2 is None
            assert ctx is self.ctx
        self.app.loop.run_until_complete(foo(self.ctx, self.event))

        @inject
        async def foo(arg_1, ctx: Context, *, arg_2=None):
            assert arg_1 is arg_2 is None
            assert ctx is self.ctx
        self.app.loop.run_until_complete(foo(self.ctx, self.event))

        @inject
        async def foo(*, ctx: Context):
            assert ctx is None
        self.app.loop.run_until_complete(foo(self.ctx, self.event))

        @inject
        async def foo(ctx_1: Context, *, ctx_2: Context):
            assert ctx_1 is self.ctx
            assert ctx_2 is None
        self.app.loop.run_until_complete(foo(self.ctx, self.event))

        @inject
        async def foo(ctx: Context, event: Event):
            assert ctx is self.ctx
            assert event is self.event
        self.app.loop.run_until_complete(foo(self.ctx, self.event))

        @inject
        async def foo(arg_1, ctx: Context, arg_2, event: Event):
            assert arg_1 is arg_2 is None
            assert ctx is self.ctx
            assert event is self.event
        self.app.loop.run_until_complete(foo(self.ctx, self.event))

        @inject
        async def foo(ctx: Context, *, event: Event):
            assert ctx is self.ctx
            assert event is None
        self.app.loop.run_until_complete(foo(self.ctx, self.event))


class TestListener(TestCase):
    def setUp(self) -> None:
        class App(Listener):
            __todos__ = ["something"]

            async def listen(self, todo: Callable[..., None]):
                todo("something", cid="Bob", age=30)

        self.app = App()

    def test_new_context(self):
        self.assertEqual(Context("Bob"), self.app.new_context("Bob"))

    def test_do(self):
        @self.app.do("something")
        async def fn(c: Context, event: Event):
            self.assertEqual("Bob", c.cid)
            self.assertEqual({"age": 30}, event.detail)
        self.app.run()

    def test_pre_post_do(self):
        ctx = self.app.new_context("Bob")

        @self.app.do("something")
        async def fn(c: Context, event: Event):
            self.assertEqual("Bob", c.cid)
            self.assertEqual({"age": 30}, event.detail)
            c.listener.todo("another", "Bob", score=100)
            result = await c.listener.todo("block_event", block=True)
            self.assertEqual(..., result)

        @self.app.do("block_event")
        async def fn(c: Context, event: Event):
            self.assertEqual("Bob", c.cid)
            self.assertEqual({"score": 100}, event.detail)
            return ...

        @self.app.do("another")
        async def fn(c: Context, event: Event):
            self.assertEqual("Bob", c.cid)
            self.assertEqual({"score": 100}, event.detail)

        @self.app.pre_do
        async def fn(c: Context):
            self.assertEqual(ctx, c)

        @self.app.post_do
        async def fn(c: Context):
            self.assertEqual(ctx, c)

        self.app.run()

    def test_error_raised(self):
        ctx = self.app.new_context("Bob")

        @self.app.do("something")
        async def fn():
            raise ValueError("something wrong")

        self.app.run()  # TODO

        @self.app.error_raise
        async def fn(c: Context, event: Event):
            self.assertEqual(ctx, c)
            self.assertEqual({"age": 30}, event.detail)
            self.assertIsInstance(ctx.errors[0], ValueError)

        self.app.run()

