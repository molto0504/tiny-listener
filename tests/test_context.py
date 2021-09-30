from unittest import TestCase

from pyevent import Context, inject, Message


class TestContext(TestCase):
    def test_ok(self):
        ctx = Context("ctx_1", foo="foo", bar=2)
        self.assertEqual("ctx_1", ctx.cid)
        self.assertEqual({"foo": "foo", "bar": 2, "_app_": None}, ctx.scope)

    def test_unique(self):
        self.assertIs(Context("req_2"), Context("req_2"))

    def test_app(self):
        ctx = Context("ctx_4", _app_=...)
        self.assertEqual(..., ctx.app)

    def test_exist(self):
        ctx = Context("ctx_5")
        self.assertTrue(ctx.exist("ctx_5"))
        self.assertFalse(ctx.exist("_not_exist_"))

    def test_drop(self):
        ctx = Context("ctx_6")
        self.assertTrue(ctx.exist("ctx_6"))

        ctx.drop("ctx_6")
        self.assertFalse(ctx.exist("ctx_6"))

    def test_call(self):
        ctx = Context("ctx_7", foo="foo")(bar=2)
        self.assertEqual({"foo": "foo", "bar": 2, "_app_": None}, ctx.scope)


class TestInject(TestCase):
    def setUp(self) -> None:
        self.ctx = Context("ctx_1")
        self.msg = Message()

    def test_inject(self):
        print()

        @inject
        def foo(ctx: Context):
            assert ctx is not None
        foo(self.ctx, self.msg)

        @inject
        def foo(arg_1, ctx: Context, arg_2):
            assert arg_1 is arg_2 is None
            assert ctx is not None

        @inject
        def foo(arg_1, ctx: Context, *, arg_2=None):
            assert arg_1 is arg_2 is None
            assert ctx is not None

        @inject
        def foo(*, ctx: Context):
            assert ctx is None
        foo(self.ctx, self.msg)

        @inject
        def foo(ctx_1: Context, *, ctx_2: Context):
            assert ctx_1 is not None
            assert ctx_2 is None
        foo(self.ctx, self.msg)

        @inject
        def foo(ctx: Context, msg: Message):
            assert ctx is not None
            assert msg is not None
        foo(self.ctx, self.msg)

        @inject
        def foo(arg_1, ctx: Context, arg_2, msg: Message):
            assert arg_1 is arg_2 is None
            assert ctx is not None
            assert msg is not None
        foo(self.ctx, self.msg)

        @inject
        def foo(ctx: Context, *, msg: Message):
            assert ctx is not None
            assert msg is None
        foo(self.ctx, self.msg)
