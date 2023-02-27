from typing import Any

import pytest

from tiny_listener import Context, EventAlreadyExists, EventNotFound, Listener, Route


@pytest.fixture
def thing_route() -> Route:
    async def thing():
        return

    return Route(name="/thing/{uid}", fn=thing)


@pytest.fixture
def alice_route() -> Route:
    async def alice():
        return

    return Route(name="/user/alice", fn=alice)


@pytest.fixture
def bob_route() -> Route:
    async def bob():
        return

    return Route(name="/user/bob", fn=bob)


@pytest.fixture
def app(thing_route: Route, alice_route: Route, bob_route: Route) -> Listener:
    class App(Listener):
        async def listen(self, *_: Any) -> None:
            ...

    app = App()
    app.routes = {
        thing_route.name: thing_route,
        alice_route.name: alice_route,
        bob_route.name: bob_route,
    }
    return app


def test_ok(app: Listener):
    ctx = Context(app, cid="test_ok", scope={"scope_key": "scope_val"})
    assert ctx.listener is app
    assert ctx.cid == "test_ok"
    assert ctx.scope == {"scope_key": "scope_val"}
    assert ctx.events == {}
    assert ctx.cache == {}


def test_alive_drop(app: Listener):
    ctx = app.new_ctx(cid="foo")

    assert ctx.is_alive is True
    assert ctx.drop() is True

    assert ctx.is_alive is False
    assert ctx.drop() is False


def test_new_event(app: Listener, thing_route: Route, alice_route: Route, bob_route: Route):
    ctx = Context(app, cid="_cid_")
    event = ctx.new_event(thing_route, {}, {})
    assert event.route is thing_route
    assert event.ctx is ctx
    # event already exist
    with pytest.raises(EventAlreadyExists):
        ctx.new_event(thing_route, {}, {})


def test_get_events(app: Listener, thing_route: Route, alice_route: Route, bob_route: Route):
    ctx = app.new_ctx()
    event_0 = ctx.new_event(thing_route, {}, {})
    event_1 = ctx.new_event(alice_route, {}, {})
    event_2 = ctx.new_event(bob_route, {}, {})
    assert [event_0, event_1, event_2] == ctx.get_events()
    assert [event_0, event_1, event_2] == ctx.get_events("/*")
    assert [event_1, event_2] == ctx.get_events("/user/*")
    # match one
    assert [event_1] == ctx.get_events("/user/alice")
    assert [event_2] == ctx.get_events("/user/bob")
    # match none
    assert [] == ctx.get_events("/user/null")


@pytest.mark.asyncio
async def test_trigger_event(app: Listener):
    ctx = app.new_ctx()
    await ctx.trigger_event("/user/bob")
    await ctx.trigger_event("/user/alice")

    with pytest.raises(EventNotFound):
        await ctx.trigger_event("/user/null")
