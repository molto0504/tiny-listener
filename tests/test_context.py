import pytest

from tiny_listener import Context, EventNotFound, Listener, Route


@pytest.fixture
def thing_route() -> Route:
    async def thing():
        return

    return Route(path="/thing/{uid}", fn=thing)


@pytest.fixture
def alice_route() -> Route:
    async def alice():
        return

    return Route(path="/user/alice", fn=alice)


@pytest.fixture
def bob_route() -> Route:
    async def bob():
        return

    return Route(path="/user/bob", fn=bob)


@pytest.fixture
def app(thing_route: Route, alice_route: Route, bob_route: Route) -> Listener:
    class App(Listener):
        async def listen(self):
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
    event = ctx.new_event(thing_route, {})
    assert event.route is thing_route
    assert event.ctx is ctx

    # call new_event twice
    assert len(ctx.events[thing_route]) == 1
    ctx.new_event(thing_route, {})
    assert len(ctx.events[thing_route]) == 2


@pytest.mark.asyncio
async def test_trigger_event(app: Listener):
    ctx = app.new_ctx()
    await ctx.trigger_event("/user/bob")
    await ctx.trigger_event("/user/alice")

    with pytest.raises(EventNotFound):
        await ctx.trigger_event("/user/null")
