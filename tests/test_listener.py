import asyncio
from typing import Any
from unittest.mock import patch

import pytest

from tiny_listener import (
    Context,
    ContextAlreadyExists,
    ContextNotFound,
    EventNotFound,
    Listener,
    Route,
)


@pytest.fixture
def app() -> Listener:
    class App(Listener):
        async def listen(self, *_: Any) -> None:
            ...

    App._instances.clear()  # noqa
    return App()


def test_ok(app: Listener) -> None:
    assert app.ctxs == {}
    assert app.routes == {}


def test_set_context_cls(app: Listener) -> None:
    class MyContext(Context):
        foo = None

    app.set_context_cls(MyContext)
    ctx = app.new_ctx()
    assert isinstance(ctx, MyContext)
    assert ctx.foo is None


def test_new_ctx(app: Listener) -> None:
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


def test_get_ctxs(app: Listener) -> None:
    assert app.ctxs == {}
    ctx = app.new_ctx("my_ctx")
    # get ctx
    assert app.get_ctx("my_ctx") is ctx
    # get ctx does not exist
    with pytest.raises(ContextNotFound):
        app.get_ctx("_not_exit_")


def test_match(app: Listener) -> None:
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


def test_on_event_callback(app: Listener) -> None:
    @app.on_event("/foo", after="/...", cfg=...)
    def foo() -> None:
        pass

    assert len(app.routes) == 1
    route = app.routes["foo"]
    assert route.path == "/foo"
    assert route.opts == {"cfg": ...}
    assert route.after == ["/..."]


def test_remove_on_event_hook(app: Listener) -> None:
    @app.on_event("/foo")
    def _foo() -> None:
        pass

    @app.on_event("/bar")
    def _bar() -> None:
        pass

    assert len(app.routes) == 2
    app.remove_on_event_hook("_foo")
    assert len(app.routes) == 1
    route = app.routes["_bar"]
    assert route.path == "/bar"


def test_startup_callback(app: Listener) -> None:
    step = []

    @app.startup
    async def step_1() -> None:
        step.append(1)

    @app.startup
    async def step_2() -> None:
        step.append(2)
        app.exit()

    with pytest.raises(SystemExit):
        app.run()

    assert step == [1, 2]


def test_shutdown_callback(app: Listener) -> None:
    step = []

    @app.shutdown
    async def step_1() -> None:
        step.append(1)

    @app.shutdown
    async def step_2() -> None:
        step.append(2)

    with pytest.raises(SystemExit):
        app.exit()

    assert step == [1, 2]


@pytest.mark.asyncio
async def test_middleware_callback(app: Listener) -> None:
    step = []

    @app.before_event
    def step_1() -> None:
        step.append(1)

    @app.on_event()
    def step_2() -> None:
        step.append(2)

    @app.after_event
    async def step_3() -> None:
        step.append(3)

    await app.trigger_event("/go")
    assert step == [1, 2, 3]


@pytest.mark.asyncio
async def test_on_error(app: Listener) -> None:
    step = []

    @app.on_event()
    async def step_1() -> None:
        step.append(1)
        raise ValueError(...)

    @app.on_error(ValueError)
    async def step_2() -> None:
        step.append(2)

    await app.trigger_event("/go")
    assert step == [1, 2]


@pytest.mark.asyncio
async def test_error_raise(app: Listener) -> None:
    @app.on_event()
    async def _value_error() -> None:
        raise ValueError(...)

    @app.on_error(KeyError)
    async def _key_error() -> None:
        ...

    with pytest.raises(ValueError):
        await app.trigger_event("/go")


def test_setup_event_loop(app: Listener) -> None:
    loop = asyncio.get_event_loop()
    assert loop is app.setup_event_loop()

    with patch("tiny_listener.listener.Listener.is_main_thread", return_value=False):
        loop = app.setup_event_loop()
        assert loop is asyncio.get_event_loop()
