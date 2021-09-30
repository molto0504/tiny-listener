from unittest import TestCase

from pyevent import Job, Jobs, Context, PyEventError, inject, Message


class TestJob(TestCase):
    def test_done(self):
        job = Job("my.test.job.1")
        self.assertFalse(job.is_done)

        job.done()
        self.assertTrue(job.is_done)


class TestJobs(TestCase):
    def test_ok(self):
        jobs = Jobs("job.foo", "job.bar")
        self.assertEqual(["job.foo", "job.bar"], list(jobs._jobs.keys()))

    def test_add(self):
        jobs = Jobs()
        self.assertEqual({}, jobs._jobs)
        jobs.add("job.foo")
        self.assertEqual(["job.foo"], list(jobs._jobs.keys()))

    def test_get(self):
        jobs = Jobs("job.foo.bar")
        self.assertEqual("job.foo.bar", jobs.get("job.foo.bar").name)
        self.assertRaises(PyEventError, jobs.get, "_not_exist_")

    def test_first(self):
        jobs = Jobs("job.foo.bar")
        self.assertEqual("job.foo.bar", jobs.first("job.foo.bar").name)
        self.assertEqual("job.foo.bar", jobs.first("job.foo*").name)
        self.assertEqual("job.foo.bar", jobs.first().name)

        jobs.first().done()
        self.assertIsNone(jobs.first())

    def test_all(self):
        jobs = Jobs("job.foo", "job.bar")
        self.assertEqual([jobs.get("job.foo"), jobs.get("job.bar")], jobs.all("job*"))
        self.assertEqual([jobs.get("job.foo"), jobs.get("job.bar")], jobs.all())
        self.assertEqual([jobs.get("job.foo")], jobs.all("job.f.*"))

        jobs.get("job.foo").done()
        self.assertEqual([jobs.get("job.bar")], jobs.all())

    def test_done(self):
        jobs = Jobs("job.foo", "job.bar")
        jobs.first().done()
        self.assertFalse(jobs.is_done("job*"))
        jobs.first().done()
        self.assertTrue(jobs.is_done("job*"))


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
