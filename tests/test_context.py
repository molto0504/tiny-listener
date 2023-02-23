from typing import Any

import pytest

from tiny_listener import Context, EventAlreadyExists, Listener


@pytest.fixture()
def app() -> Listener:
    class App(Listener):
        async def listen(self, *_: Any) -> None:
            ...

    app = App()

    @app.on_event(name="/thing/{uid}")
    async def _thing() -> None:
        ...

    @app.on_event(name="/user/foo")
    async def _user_foo() -> None:
        ...

    @app.on_event(name="/user/bar")
    async def _user_bar() -> None:
        ...

    return app


def test_ok(app: Listener) -> None:
    ctx = Context(app, cid="test_ok", scope={"scope_key": "scope_val"})
    assert ctx.cid == "test_ok"
    assert ctx.scope == {"scope_key": "scope_val"}
    assert ctx.events == {}
    assert ctx.cache == {}


def test_alive_drop(app: Listener) -> None:
    ctx = app.new_ctx(cid="foo")

    assert ctx.is_alive is True
    assert ctx.drop() is True

    assert ctx.is_alive is False
    assert ctx.drop() is False


def test_new_event(app: Listener) -> None:
    ctx = Context(app, cid="_cid_")
    route = app.routes[0]
    event = ctx.new_event(name="/thing/1", route=route)
    assert event.route is app.routes[0]
    assert event.route is route
    assert event.ctx is ctx
    # event already exist
    with pytest.raises(EventAlreadyExists):
        ctx.new_event(name="/thing/1", route=route)


def test_get_events(app: Listener) -> None:
    ctx = Context(app, cid="_cid_")
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


@pytest.mark.asyncio
async def test_trigger_event(app: Listener) -> None:
    ctx = Context(listener=app, cid="_cid_", scope={"scope_key": "scope_val"})
    await ctx.trigger_event("/thing/1")
