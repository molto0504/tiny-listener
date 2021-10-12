from unittest import TestCase

from tiny_listener import Context, inject, Listener, Event


class TestInject(TestCase):
    def setUp(self) -> None:
        class App(Listener):
            __todos__ = ["foo"]

        self.ctx = Context("ctx_inject", _listener_=App())
        self.event = self.ctx.events["foo"]

    def test_inject(self):
        @inject
        def foo(ctx: Context):
            assert ctx is self.ctx
        foo(self.ctx, self.event)

        @inject
        def foo(arg_1, ctx: Context, arg_2):
            assert arg_1 is arg_2 is None
            assert ctx is self.ctx
        foo(self.ctx, self.event)

        @inject
        def foo(arg_1, ctx: Context, *, arg_2=None):
            assert arg_1 is arg_2 is None
            assert ctx is self.ctx
        foo(self.ctx, self.event)

        @inject
        def foo(*, ctx: Context):
            assert ctx is None
        foo(self.ctx, self.event)

        @inject
        def foo(ctx_1: Context, *, ctx_2: Context):
            assert ctx_1 is self.ctx
            assert ctx_2 is None
        foo(self.ctx, self.event)

        @inject
        def foo(ctx: Context, event: Event):
            assert ctx is self.ctx
            assert event is self.event
        foo(self.ctx, self.event)

        @inject
        def foo(arg_1, ctx: Context, arg_2, event: Event):
            assert arg_1 is arg_2 is None
            assert ctx is self.ctx
            assert event is self.event
        foo(self.ctx, self.event)

        @inject
        def foo(ctx: Context, *, event: Event):
            assert ctx is self.ctx
            assert event is None
        foo(self.ctx, self.event)
