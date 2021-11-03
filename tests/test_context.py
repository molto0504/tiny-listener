import pytest
from unittest import TestCase

from tiny_listener import Context, Listener, Event, Route


class TestContext(TestCase):
    def test_ok(self):
        # global context
        ctx = Context(foo="foo", bar=2)
        self.assertEqual("_global_", ctx.cid)
        self.assertEqual("foo", ctx.scope["foo"])
        self.assertEqual(2, ctx.scope["bar"])
        self.assertEqual({}, ctx.events)
        # request context
        ctx = Context(cid="req_1", foo="foo", bar=2)
        self.assertEqual("req_1", ctx.cid)
        self.assertEqual("foo", ctx.scope["foo"])
        self.assertEqual(2, ctx.scope["bar"])
        self.assertEqual({}, ctx.events)

    def test_unique(self):
        self.assertIs(Context("req_2"), Context("req_2"))

    def test_listener(self):
        ctx = Context("ctx_3", _listener_=None)
        self.assertEqual(None, ctx.listener)

    def test_exist(self):
        ctx = Context("ctx_4")
        self.assertTrue(ctx.exist("ctx_4"))
        self.assertFalse(ctx.exist("_not_exist_"))

    def test_drop(self):
        ctx = Context("ctx_6")
        self.assertTrue(ctx.exist("ctx_6"))

        ctx.drop("ctx_6")
        self.assertFalse(ctx.exist("ctx_6"))

    def test_call(self):
        ctx = Context("ctx_7", foo="foo")(bar=2)
        self.assertEqual("foo", ctx.scope["foo"])
        self.assertEqual(2, ctx.scope["bar"])

    def test_events(self):
        ctx = Context("ctx_9")
        event_1 = ctx.new_event("/user/foo")
        event_2 = ctx.new_event("/user/bar")
        # match all
        self.assertEqual([event_1, event_2], ctx.get_events())
        self.assertEqual([event_1, event_2], ctx.get_events("/"))
        self.assertEqual([event_1, event_2], ctx.get_events("/user/*"))
        # match one
        self.assertEqual([event_1], ctx.get_events("/user/foo"))
        self.assertEqual([event_2], ctx.get_events("/user/bar"))
        # match none
        self.assertEqual([], ctx.get_events("/user/baz"))

    def test_new_event(self):
        ctx = Context("ctx_10")
        self.assertEqual(0, len(ctx.events))
        event = ctx.new_event("/event/foo")
        self.assertEqual(event, ctx.events["/event/foo"])


class TestEvent(TestCase):
    def setUp(self) -> None:
        class App(Listener):
            def listen(self, _): ...

        app = App()
        self.ctx = app.new_context("ctx_event")
        self.event_foo = self.ctx.new_event("/user/foo")
        self.event_bar = self.ctx.new_event("/user/bar")

    def test_ok(self):
        self.assertEqual("/user/foo", self.event_foo.name)
        self.assertEqual({}, self.event_foo.data)
        self.assertEqual(set(), self.event_foo.parents)
        self.assertFalse(self.event_foo.trigger.is_set())

    def test_ctx(self):
        self.assertIs(self.ctx, self.event_foo.ctx)

    def test_parents(self):
        async def _cb(): ...

        # match all
        for pats in [
            [""],
            ["/"],
            ["/user/*"],
            ["/user/*", "", "/user/foo"],
            ["/user/foo", "/user/bar"],
            ["", "/user/_not_exist_"],
        ]:
            event = Event(name="foo", ctx=self.ctx, route=Route("/", _cb, parents=pats))
            self.assertEqual({self.event_foo, self.event_bar}, event.parents)
        # match one
        for pats in [
            ["/user/foo"],
            ["/user/foo", "/user/f"]
        ]:
            event = Event(name="foo", ctx=self.ctx, route=Route("/", _cb, parents=pats))
            self.assertEqual({self.event_foo}, event.parents)
        # match none
        for pats in [
            [],
            ["/user/_not_exist_"],
            ["/user/_not_exist_foo", "/user/_not_exist_bar"],
        ]:
            event = Event(name="foo", ctx=self.ctx, route=Route("/", _cb, parents=pats))
            self.assertEqual(set(), event.parents)


@pytest.mark.asyncio
async def test_event_trigger(event_loop):
    class App(Listener):
        def listen(self, _): ...

    async def _cb(): ...

    app = App()
    ctx = app.new_context("ctx_trigger")
    event_foo = ctx.new_event("/user/foo")
    event_bar = ctx.new_event("/user/bar", route=Route("/", fn=_cb, parents=["/user/foo"]))

    assert event_foo.is_done is False
    event_loop.call_later(0.1, lambda: event_foo.done())
    async with event_bar:
        pass
    assert event_foo.is_done is True
