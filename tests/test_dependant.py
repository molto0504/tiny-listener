import asyncio
from unittest import TestCase

import pytest

from tiny_listener import Depends, as_hook, Event


class FakeEvent:
    def __init__(self):
        class FakeContext:
            def __init__(self):
                self.cache = {}

        self.ctx = FakeContext()


class TestDepends(TestCase):
    def test_ok(self):
        def normal_func(): pass

        dep = Depends(fn=normal_func)
        self.assertFalse(dep.is_coro)
        self.assertTrue(asyncio.iscoroutinefunction(dep.hook))
        self.assertTrue(dep.use_cache)

    def test_call(self):
        def normal_func():
            raise ValueError()

        dep = Depends(fn=normal_func)
        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(dep.hook(FakeEvent()))  # type: ignore
        with pytest.raises(ValueError):
            loop.run_until_complete(task)


class TestAsHook(TestCase):
    def test_ok(self):
        def normal_func(): pass
        async def async_func(): pass

        self.assertTrue(asyncio.iscoroutinefunction(as_hook(normal_func)))
        self.assertTrue(asyncio.iscoroutinefunction(as_hook(async_func)))

    def test_run_simple_normal_hook(self):
        def my_dep():
            raise ValueError()

        def normal_func(*, _=Depends(my_dep)):
            pass

        hook = as_hook(fn=normal_func)
        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(hook(FakeEvent()))  # type: ignore
        with pytest.raises(ValueError):
            loop.run_until_complete(task)

    def test_run_complex_normal_hook(self):
        fake_event = FakeEvent()

        def my_dep(event: Event):
            assert event is fake_event
            return ...

        def normal_func(event: Event, *, dep=Depends(my_dep)):
            assert event is fake_event
            assert dep is ...

        hook = as_hook(fn=normal_func)
        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(hook(fake_event))  # type: ignore
        loop.run_until_complete(task)

    def test_run_simple_async_hook(self):
        async def my_dep():
            raise ValueError()

        async def normal_func(*, _=Depends(my_dep)):
            pass

        hook = as_hook(fn=normal_func)
        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(hook(FakeEvent()))  # type: ignore
        with pytest.raises(ValueError):
            loop.run_until_complete(task)

    def test_run_complex_async_hook(self):
        fake_event = FakeEvent()

        async def my_dep(event: Event):
            assert event is fake_event
            return ...

        async def normal_func(event: Event, *, dep=Depends(my_dep)):
            assert event is fake_event
            assert dep is ...

        hook = as_hook(fn=normal_func)
        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(hook(fake_event))  # type: ignore
        loop.run_until_complete(task)

    def test_signature(self):
        fake_event = FakeEvent()

        def normal_func(event_1: Event, event_2: Event, field_1, *, field_2=None):
            assert event_1 is event_2 is fake_event
            assert field_1 is field_2 is None

        hook = as_hook(fn=normal_func)
        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(hook(fake_event))  # type: ignore
        loop.run_until_complete(task)

    def test_use_cache(self):
        seq = 0

        def my_dep():
            nonlocal seq
            seq += 1
            return seq

        def func_use_cache(*, dep_1=Depends(my_dep, use_cache=True), dep_2=Depends(my_dep, use_cache=True)):
            assert dep_1 == dep_2 == 1

        loop = asyncio.get_event_loop()
        hook = as_hook(fn=func_use_cache)
        task = asyncio.ensure_future(hook(FakeEvent()))  # type: ignore
        loop.run_until_complete(task)

    def test_without_cache(self):
        seq = 0

        def my_dep():
            nonlocal seq
            seq += 1
            return seq

        def func_use_cache(*, dep_1=Depends(my_dep, use_cache=False), dep_2=Depends(my_dep, use_cache=False)):
            assert dep_1 == 1
            assert dep_2 == 2

        loop = asyncio.get_event_loop()
        hook = as_hook(fn=func_use_cache)
        task = asyncio.ensure_future(hook(FakeEvent()))  # type: ignore
        loop.run_until_complete(task)
