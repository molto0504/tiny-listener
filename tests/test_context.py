import asyncio

import pytest

from tiny_listener import Context, Listener


@pytest.fixture(scope="module")
def app():
    class App(Listener):
        async def listen(self): ...

    app = App()

    @app.on_event(path="/thing/{uid}")
    async def f(): ...

    @app.on_event(path="/user/foo")
    async def f(): ...

    @app.on_event(path="/user/bar")
    async def f(): ...

    return app


def test_ok(app):
    # with id
    ctx = Context(listener=app, cid="test_ok", scope={"scope_key": "scope_val"})
    assert ctx.cid == "test_ok"
    assert ctx.listener == app
    assert ctx.scope == {"scope_key": "scope_val"}
    assert ctx.events == {}
    assert ctx.cache == {}
    # without id
    ctx = Context(listener=app)
    assert ctx.cid == "__global__"
    assert ctx.listener == app
    assert ctx.scope == {}
    assert ctx.events == {}
    assert ctx.cache == {}


def test_alive_drop(app):
    ctx = Context(listener=app, cid="test_alive_drop")
    assert ctx.is_alive is False
    app.add_ctx(ctx)
    assert ctx.is_alive is True

    assert ctx.drop() is True
    assert ctx.is_alive is False
    assert ctx.drop() is False


def test_new_event(app):
    ctx = Context(listener=app)
    route = app.routes[0]
    event = ctx.new_event(name="/thing/1", route=route)
    assert event.route is app.routes[0]
    assert event.route is route
    assert event.ctx is ctx


def test_get_events(app):
    ctx = Context(listener=app)
    event_1 = ctx.new_event(name="/user/foo", route=app.routes[1])
    event_2 = ctx.new_event(name="/user/bar", route=app.routes[2])
    # match all
    assert [event_1, event_2] == ctx.get_events()
    assert [event_1, event_2] == ctx.get_events("/")
    assert [event_1, event_2] == ctx.get_events("/user/*")
    # match one
    assert [event_1] == ctx.get_events("/user/foo")
    assert [event_2] == ctx.get_events("/user/bar")
    # match none
    assert [] == ctx.get_events("/user/baz")


def test_fire(app):
    ctx = Context(listener=app, scope={"scope_key": "scope_val"})
    assert isinstance(ctx.fire("/thing/1"), asyncio.Task)
