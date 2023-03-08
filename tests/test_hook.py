from typing import Any, Dict

import pytest

from tiny_listener import (
    Context,
    Data,
    Depends,
    Event,
    EventDataError,
    Listener,
    Param,
    PathParamsError,
    depend,
)


@pytest.fixture
def fake_context() -> Context:
    class FakeContext:
        cache = {}

    return FakeContext()  # noqa


@pytest.fixture
def fake_event(fake_context) -> Event:
    class FakeEvent:
        data = {}
        ctx = fake_context

    return FakeEvent()  # noqa


@pytest.mark.parametrize("caller", [Depends, depend])
def test_depend_ok(caller):
    async def normal_func():
        pass

    dep = caller(normal_func)
    assert dep.use_cache is True
    dep = caller(normal_func, use_cache=False)
    assert dep.use_cache is False


@pytest.mark.asyncio
@pytest.mark.parametrize("caller", [Depends, depend])
async def test_call_dep(caller, fake_event):
    async def get_data():
        return "data"

    dep = caller(get_data)
    assert await dep(fake_event, {}) == "data"


@pytest.mark.asyncio
@pytest.mark.parametrize("caller", [Depends, depend])
async def test_run_hook_with_depends(caller, fake_event, fake_context):
    fake_event.data = {"age": 18}

    async def get_user(event: Event, username: Param, age: Data, ctx: Context):
        assert event is fake_event
        assert event.ctx is ctx is fake_context
        return {"username": username, "age": age}

    async def get_username(event: Event, user: Dict = caller(get_user)):
        assert event is fake_event
        assert user == {"username": "bob", "age": 18}
        return user.get("username")

    dep = caller(get_username)
    assert await dep(fake_event, {"username": "bob"}) == "bob"


@pytest.mark.asyncio
@pytest.mark.parametrize("caller", [Depends, depend])
async def test_run_complex_hook(caller, fake_event):
    async def get_user(event: Event):
        assert event is fake_event
        return {"username": "bob"}

    async def get_data(event: Event):
        assert event is fake_event
        return {"bob": "bob's data"}

    async def get_user_data(event: Event, user: Dict = caller(get_user), data: Dict = caller(get_data)):
        assert event is fake_event
        username = user.get("username")
        return data[username]

    dep = caller(get_user_data)
    assert await dep(fake_event, {}) == "bob's data"


@pytest.mark.asyncio
@pytest.mark.parametrize("caller", [Depends, depend])
async def test_signature(caller, fake_event):
    async def get_user():
        return {"username": "bob"}

    async def get_user_name(
        event_1: Event,
        event_2: Event,
        field_1,
        dep_1=caller(get_user),
        *,
        field_2: Any = None,
        dep_2=caller(get_user),
    ):
        assert event_1 is event_2 is fake_event
        assert field_1 is field_2 is None
        assert dep_1 == dep_2 == {"username": "bob"}
        return dep_1.get("username")

    dep = caller(get_user_name)
    assert await dep(fake_event, {}) == "bob"


@pytest.mark.asyncio
@pytest.mark.parametrize("caller", [Depends, depend])
async def test_dep_with_cache(caller, fake_event):
    async def get_user():
        return {"username": "bob"}

    async def get_username(dep_1=caller(get_user, use_cache=True), dep_2=caller(get_user, use_cache=True)):
        assert dep_1 is dep_2  # dep_1 and dep_2 are the same object, because use_cache=True
        return dep_1.get("username")

    dep = caller(get_username)
    assert await dep(fake_event, {}) == "bob"


@pytest.mark.asyncio
@pytest.mark.parametrize("caller", [Depends, depend])
async def test_dep_without_cache(caller, fake_event):
    async def get_user():
        return {"username": "bob"}

    async def get_username(dep_1=caller(get_user, use_cache=False), dep_2=caller(get_user, use_cache=False)):
        assert dep_1 == dep_2
        assert dep_1 is not dep_2  # dep_1 and dep_2 are different objects, because use_cache=False
        return dep_1.get("username")

    dep = caller(get_username)
    assert await dep(fake_event, {}) == "bob"


def test_bad_callback():
    class App(Listener):
        async def listen(self):
            ...

    app = App()

    @app.on_event()
    async def foo():
        ...

    with pytest.raises(TypeError):

        @app.on_event()
        def bar():  # use normal function instead of async function
            ...


@pytest.mark.asyncio
@pytest.mark.parametrize("caller", [Depends, depend])
async def test_param_or_data_not_found(caller, fake_event):
    class App(Listener):
        async def listen(self):
            ...

    app = App()

    @app.on_event()
    async def foo(event: Event, username: Param, age: Data):
        assert event is fake_event
        return {"username": username, "age": age}

    dep = caller(foo)
    with pytest.raises(PathParamsError):
        await dep(fake_event, {})  # path params not found

    with pytest.raises(EventDataError):
        await dep(fake_event, {"username": "bob"})  # event data not found

    fake_event.data = {"age": 18}
    assert await dep(fake_event, {"username": "bob"}) == {"username": "bob", "age": 18}  # ok
