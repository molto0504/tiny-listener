from unittest import TestCase

from tiny_listener import Job, Jobs


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
        self.assertRaises(ValueError, jobs.get, "_not_exist_")

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

    def test_len(self):
        jobs = Jobs("job.foo", "job.bar")
        self.assertEqual(2, len(jobs))
