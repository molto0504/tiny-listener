import asyncio
import os
import signal
import threading
from unittest.mock import PropertyMock, patch

import pytest

from tiny_listener import (
    Context,
    ContextAlreadyExists,
    ContextNotFound,
    EventAlreadyExists,
    EventNotFound,
    Listener,
    ListenerNotFound,
    Route,
    get_current_running_listener,
)


@pytest.fixture
def app() -> Listener:
    class App(Listener):
        async def listen(self):
            ...

    App._instances.clear()  # noqa
    return App()


def test_listener(app: Listener):
    assert app.ctxs == {}
    assert app.routes == {}


def test_set_context_cls(app: Listener):
    class MyContext(Context):
        foo = None

    app.set_context_cls(MyContext)
    ctx = app.new_ctx()
    assert isinstance(ctx, MyContext)
    assert ctx.foo is None


def test_new_ctx(app: Listener):
    assert app.ctxs == {}

    # new ctx not exist
    ctx = app.new_ctx("my_ctx", scope={"foo": ...})
    assert app.ctxs == {"my_ctx": ctx}
    assert app.ctxs[ctx.cid].scope == {"foo": ...}

    # new ctx already exist
    with pytest.raises(ContextAlreadyExists):
        app.new_ctx("my_ctx")

    # ctx with auto increment id
    assert len(app.ctxs) == 1
    app.new_ctx()
    assert len(app.ctxs) == 2
    app.new_ctx()
    assert len(app.ctxs) == 3


def test_get_ctxs(app: Listener):
    assert app.ctxs == {}
    ctx = app.new_ctx("my_ctx")
    # get ctx
    assert app.get_ctx("my_ctx") is ctx
    # get ctx does not exist
    with pytest.raises(ContextNotFound):
        app.get_ctx("_not_exit_")


def test_match(app: Listener):
    route_user_list = Route("/users", fn=lambda: ...)
    route_user_detail = Route("/user/{name}", fn=lambda: ...)
    app.routes = {route_user_detail.name: route_user_detail, route_user_list.name: route_user_list}

    route, params = app.match_route("/users")
    assert route is route_user_list
    assert params == {}

    route, params = app.match_route("/user/bob")
    assert route is route_user_detail
    assert "name" in params

    with pytest.raises(EventNotFound):
        app.match_route("/_not_exist_")


@pytest.mark.asyncio
async def test_on_event(app: Listener):
    result = []

    @app.on_event("/step_1")
    async def step_1():
        result.append("step_1_done")

    @app.on_event("/step_2", after="step_1", cfg={})
    async def step_2():
        result.append("step_2_done")

    assert len(app.routes) == 2
    route = app.routes["step_2"]
    assert route.path == "/step_2"
    assert route.opts == {"cfg": {}}
    assert route.after == ["step_1"]
    with pytest.raises(EventAlreadyExists):

        @app.on_event("/step_2")
        async def step_2():  # noqa
            pass

    ctx = app.new_ctx()
    await ctx.trigger_event("/step_1", timeout=1)
    await ctx.trigger_event("/step_2", timeout=1)
    assert result == ["step_1_done", "step_2_done"]


def test_remove_on_event_hook(app: Listener):
    @app.on_event("/foo")
    async def foo():
        pass

    @app.on_event("/bar")
    async def bar():
        pass

    assert len(app.routes) == 2
    assert app.remove_on_event_hook("foo") is True
    assert len(app.routes) == 1
    assert app.remove_on_event_hook("foo") is False
    assert len(app.routes) == 1
    assert app.routes["bar"].path == "/bar"


def test_startup_shutdown(app: Listener):
    step = []

    @app.startup
    async def step_1():
        step.append(1)

    @app.startup
    async def step_2():
        step.append(2)
        os.kill(os.getpid(), signal.SIGINT)

    app.run()
    assert step == [1, 2]


def test_graceful_shutdown(app: Listener):
    step = []

    @app.startup
    async def step_0():
        step.append(0)
        os.kill(os.getpid(), signal.SIGINT)

    @app.shutdown
    async def step_1():
        step.append(1)

    @app.shutdown
    async def step_2():
        step.append(2)

    app.run()

    assert step == [0, 1, 2]


def test_force_shutdown(app: Listener):
    with patch.object(app._Listener__exiting, "is_set", return_value=True):  # noqa

        @app.startup
        async def step_0():
            os.kill(os.getpid(), signal.SIGINT)

        with pytest.raises(RuntimeError):
            app.run()


@pytest.mark.asyncio
async def test_middleware_callback(app: Listener):
    step = []

    @app.before_event
    async def step_1():
        step.append(1)

    @app.on_event()
    async def step_2():
        step.append(2)

    @app.after_event
    async def step_3():
        step.append(3)

    await app.trigger_event("/go")
    assert step == [1, 2, 3]


@pytest.mark.asyncio
async def test_on_error(app: Listener):
    step = []

    @app.on_event()
    async def step_1():
        step.append(1)
        raise ValueError(...)

    @app.on_error(ValueError)
    async def step_2():
        step.append(2)

    await app.trigger_event("/go")
    assert step == [1, 2]


@pytest.mark.asyncio
async def test_error_raise(app: Listener):
    @app.on_event()
    async def _value_error():
        raise ValueError(...)

    @app.on_error(KeyError)
    async def _key_error():
        ...

    with pytest.raises(ValueError):
        await app.trigger_event("/go")


def test_setup_event_loop(app: Listener):
    loop = asyncio.get_event_loop()
    assert loop is app.setup_event_loop()

    with patch("tiny_listener.listener.Listener.is_main_thread", return_value=False):
        loop = app.setup_event_loop()
        assert loop is asyncio.get_event_loop()


def test_get_current_running_listener(app: Listener):
    with pytest.raises(ListenerNotFound):
        get_current_running_listener()

    instances = {threading.get_ident(): app}
    with patch("tiny_listener.listener.Listener._instances", new_callable=PropertyMock, return_value=instances):
        assert get_current_running_listener() is app
