import asyncio
from typing import Any, Dict, Literal
from unittest import TestCase

import pytest

from tiny_listener import Depends, Event


class FakeEvent:
    def __init__(self) -> None:
        class FakeContext:
            def __init__(self) -> None:
                self.cache: Dict[Depends, Any] = {}

        self.ctx = FakeContext()


class TestHookDepends(TestCase):
    def setUp(self) -> None:
        self.fake_event = FakeEvent()
        self.loop = asyncio.get_event_loop()

    def test_ok(self) -> None:
        def normal_func() -> None:
            pass

        dep = Depends(fn=normal_func)
        self.assertTrue(dep.use_cache)

    def test_call(self) -> None:
        def normal_func() -> None:
            raise ValueError()

        dep = Depends(fn=normal_func)
        with pytest.raises(ValueError):
            self.loop.run_until_complete(dep(self.fake_event))  # type: ignore

    def test_run_simple_normal_hook(self) -> None:
        def my_dep() -> None:
            raise ValueError()

        def normal_func(_: Any = Depends(my_dep)) -> None:
            pass

        dep = Depends(fn=normal_func)
        with pytest.raises(ValueError):
            self.loop.run_until_complete(dep(self.fake_event))  # type: ignore

    def test_run_complex_normal_hook(self) -> None:
        def my_dep(event: Event) -> object:
            assert event is self.fake_event
            return ...

        def fn(event: Event, foo=Depends(my_dep)) -> None:
            assert event is self.fake_event
            assert foo is ...

        dep = Depends(fn=fn)
        self.loop.run_until_complete(dep(self.fake_event))  # type: ignore

    def test_run_simple_async_hook(self) -> None:
        async def my_dep() -> None:
            raise ValueError()

        async def fn(_: Any = Depends(my_dep)) -> None:
            pass

        dep = Depends(fn=fn)
        with pytest.raises(ValueError):
            self.loop.run_until_complete(dep(self.fake_event))  # type: ignore

    def test_run_complex_async_hook(self) -> None:
        async def my_dep(event: Event) -> object:
            assert event is self.fake_event
            return ...

        async def fn(event: Event, foo=Depends(my_dep)) -> None:
            assert event is self.fake_event
            assert foo is ...

        dep = Depends(fn=fn)
        self.loop.run_until_complete(dep(self.fake_event))  # type: ignore

    def test_signature(self) -> None:
        async def my_dep() -> object:
            return ...

        def fn(
            event_1: Event,
            event_2: Event,
            field_1,
            dep_1=Depends(my_dep),
            *,
            field_2: Any = None,
            dep_2=Depends(my_dep),
        ) -> None:
            assert event_1 is event_2 is self.fake_event
            assert field_1 is field_2 is None
            assert dep_1 is dep_2 is ...

        dep = Depends(fn=fn)
        self.loop.run_until_complete(dep(self.fake_event))  # type: ignore

    def test_use_cache(self) -> None:
        seq = 0

        def my_dep() -> int:
            nonlocal seq
            seq += 1
            return seq

        def fn(dep_1: int = Depends(my_dep, use_cache=True), dep_2: int = Depends(my_dep, use_cache=True)) -> None:
            assert dep_1 == dep_2 == 1

        dep = Depends(fn=fn)
        self.loop.run_until_complete(dep(self.fake_event))  # type: ignore

    def test_without_cache(self) -> None:
        seq = 0

        def my_dep() -> int:
            nonlocal seq
            seq += 1
            return seq

        def fn(
            dep_1: int = Depends(my_dep, use_cache=False),
            dep_2: int = Depends(my_dep, use_cache=False),
        ) -> None:
            assert dep_1 == 1
            assert dep_2 == 2

        dep = Depends(fn=fn)
        self.loop.run_until_complete(dep(self.fake_event))  # type: ignore

    def test_async_normal_mix(self) -> None:
        def get_foo() -> Literal["foo"]:
            return "foo"

        async def get_bar() -> Literal["bar"]:
            return "bar"

        def fn(foo: str = Depends(get_foo), bar: str = Depends(get_bar)) -> None:
            assert foo == "foo"
            assert bar == "bar"

        dep = Depends(fn=fn)
        self.loop.run_until_complete(dep(self.fake_event))  # type: ignore
