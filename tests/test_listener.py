from unittest import TestCase
from typing import Callable

from tiny_listener import Context, Listener, Event


class TestListener(TestCase):
    def setUp(self) -> None:
        class App(Listener):
            async def listen(self, todo: Callable[..., None]):
                todo("something", cid="Bob", data={"age": 30})

        self.app = App()

    def test_new_context(self):
        self.assertEqual(Context("Bob"), self.app.new_context("Bob"))

    def test_do(self):
        @self.app.do("something")
        async def fn(c: Context, event: Event):
            self.assertEqual("Bob", c.cid)
            self.assertEqual({"age": 30}, event.data)

        self.app.loop.run_until_complete(self.app.listen(self.app.todo))

    def test_pre_post_do(self):
        ctx = self.app.new_context("Bob")

        @self.app.do("something")
        async def fn(c: Context, event: Event):
            self.assertEqual("Bob", c.cid)
            self.assertEqual({"age": 30}, event.data)
            c.listener.todo("another", "Bob", data={"score": 100})
            result = await c.listener.todo("block_event", block=True)
            self.assertEqual(..., result)

        @self.app.do("block_event")
        async def fn(c: Context, event: Event):
            self.assertEqual("Bob", c.cid)
            self.assertEqual({"score": 100}, event.data)
            return ...

        @self.app.do("another")
        async def fn(c: Context, event: Event):
            self.assertEqual("Bob", c.cid)
            self.assertEqual({"score": 100}, event.data)

        @self.app.pre_do
        async def fn(c: Context):
            self.assertEqual(ctx, c)

        @self.app.post_do
        async def fn(c: Context):
            self.assertEqual(ctx, c)

        self.app.loop.run_until_complete(self.app.listen(self.app.todo))

    def test_error_raised(self):
        ctx = self.app.new_context("Bob")

        @self.app.do("something")
        async def fn():
            raise ValueError("something wrong")

        self.app.loop.run_until_complete(self.app.listen(self.app.todo))

        @self.app.error_raise
        async def fn(c: Context, event: Event):
            self.assertEqual(ctx, c)
            self.assertEqual({"age": 30}, event.data)
            self.assertIsInstance(ctx.errors[0], ValueError)

        self.app.loop.run_until_complete(self.app.listen(self.app.todo))
