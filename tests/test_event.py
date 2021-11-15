import pytest

from tiny_listener import Context, Listener, Event


@pytest.fixture()
def app():
    class App(Listener):
        async def listen(self, _): ...

    app = App()

    async def endpoint(): ...
    @app.do(path="/user/{name}", fn=endpoint, opts={"opts_1": "foo"}, parents=["/parent"])
    async def f(): ...

    @app.do(path="/parent", fn=endpoint, opts={"opts_2": "bar"}, parents=[])
    async def f(): ...

    return app


@pytest.fixture()
def ctx(app):
    return Context(listener=app, scope={"scope_1": "foo", "scope_2": "bar"})


def test_ok(ctx):
    route = ctx.listener.routes[0]
    event = Event(name="/user/bob", ctx=ctx, route=route)
    assert event.ctx is ctx
    assert event.route is route
    assert event.name == "/user/bob"
    assert event.data == {}
    assert event.parents == set()
    assert event.is_done is False


def test_ok_from_ctx(ctx):
    route = ctx.listener.routes[0]
    event = ctx.new_event(name="/user/bob", route=route, data={"data_1": "foo"})
    assert event.ctx is ctx
    assert event.route is route
    assert event.name == "/user/bob"
    assert event.data == {"data_1": "foo"}
    assert event.is_done is False
    assert event.parents == set()


@pytest.mark.asyncio
async def test_done(event_loop, ctx):
    event = Event(name="/user/bob", ctx=ctx, route=ctx.listener.routes[0])
    assert event.is_done is False

    event_loop.call_later(0.1, lambda: event.done())
    await event.wait()
    assert event.is_done is True


def test_parents(ctx):
    parent = ctx.new_event(name="/parent", route=ctx.listener.routes[1])
    event = ctx.new_event(name="/user/bob", route=ctx.listener.routes[0], data={"data_1": "foo"})
    assert event.parents == {parent}
