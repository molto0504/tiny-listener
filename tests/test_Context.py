from unittest import TestCase

from pyevent import Job, Jobs, Context, PyEventError


class TestJob(TestCase):
    def test_done(self):
        job = Job("my.test.job.1")
        self.assertFalse(job.is_done)

        job.done()
        self.assertTrue(job.is_done)


class TestJobs(TestCase):
    def test_ok(self):
        jobs = Jobs("job_1", "job_2")
        self.assertEqual(["job_1", "job_2"], list(jobs._jobs.keys()))

    def test_add(self):
        jobs = Jobs()
        self.assertEqual({}, jobs._jobs)
        jobs.add("job_1")
        self.assertEqual(["job_1"], list(jobs._jobs.keys()))

    def test_get(self):
        jobs = Jobs("job.foo.bar")
        self.assertEqual("job.foo.bar", jobs.get("job.foo.bar").name)
        self.assertRaises(PyEventError, jobs.get, "_not_exist_")

    def test_first(self):
        jobs = Jobs("job.foo.bar")
        self.assertEqual("job.foo.bar", jobs.first("job.foo.bar").name)
        self.assertEqual("job.foo.bar", jobs.first("job.foo*").name)
        self.assertEqual("job.foo.bar", jobs.first().name)
        self.assertRaises(PyEventError, jobs.first, "_not_exist_")

    def test_done(self):
        jobs = Jobs("job.foo", "job.bar")
        jobs.first().done()
        self.assertFalse(jobs.is_done("job*"))
        jobs.first().done()
        self.assertTrue(jobs.is_done("job*"))


class TestContext(TestCase):
    def test_ok(self):
        req = Context("req_01", foo="foo", bar=2)
        self.assertEqual("req_01", req.req_id)
        self.assertEqual({"foo": "foo", "bar": 2}, req.scope)

    def test_unique(self):
        self.assertIs(Context("req_01"), Context("req_01"))

    def test_call(self):
        req = Context("req_01", foo="foo")(bar=2)
        self.assertEqual({"foo": "foo", "bar": 2}, req.scope)
