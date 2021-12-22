import asyncio
import pytest

from tiny_listener import Context, Listener, Event


@pytest.fixture()
def app():
    class App(Listener):
        async def listen(self, _): ...
    app = App()

    @app.on_event(path="/thing")
    async def f(): ...

    return app


@pytest.fixture()
def ctx(app):
    return Context(listener=app,
                   scope={
                       "scope_1": "foo",
                       "scope_2": "bar"
                   })


def test_ok(ctx):
    route = ctx.listener.routes[0]
    event = Event(name="/thing", ctx=ctx, route=route)
    assert event.ctx is ctx
    assert event.route is route
    assert event.name == "/thing"
    assert event.data == {}
    assert event.parents == set()
    assert event.is_done is False


def test_ok_from_ctx(ctx):
    route = ctx.listener.routes[0]
    event = ctx.new_event(name="/thing",
                          route=route,
                          data={"data_1": "foo"})
    assert event.ctx is ctx
    assert event.route is route
    assert event.name == "/thing"
    assert event.data == {"data_1": "foo"}
    assert event.is_done is False
    assert event.parents == set()


@pytest.mark.asyncio
async def test_done(event_loop, ctx):
    event = Event(name="/thing",
                  ctx=ctx,
                  route=ctx.listener.routes[0])

    assert event.is_done is False
    event_loop.call_later(0.1, lambda: event.done())
    await event.wait_until_done()
    assert event.is_done is True


@pytest.mark.asyncio
async def test_timeout(event_loop, ctx):
    event = Event(name="/thing",
                  ctx=ctx,
                  route=ctx.listener.routes[0])
    assert event.is_done is False
    with pytest.raises(asyncio.futures.TimeoutError):
        await event.wait_until_done(timeout=0.1)
    assert event.is_done is False


@pytest.fixture()
def ex_ctx(ctx):
    @ctx.listener.on_event(path="/user/alice")
    async def f(): ...

    @ctx.listener.on_event(path="/user/bob")
    async def f(): ...

    return ctx


def test_parents_1(ex_ctx):
    @ex_ctx.listener.on_event("/home", parents=["/user/*"])
    async def home(): ...

    event_bob = ex_ctx.new_event(name="/user/bob", route=ex_ctx.listener.routes[-2])
    event_alice = ex_ctx.new_event(name="/user/alice", route=ex_ctx.listener.routes[-3])
    event = ex_ctx.new_event(name="/home", route=ex_ctx.listener.routes[-1])
    assert {event_alice, event_bob} == event.parents


def test_parents_2(ex_ctx):
    @ex_ctx.listener.on_event("/home", parents=["/user/b"])
    async def home(): ...

    event_bob = ex_ctx.new_event(name="/user/bob", route=ex_ctx.listener.routes[-2])
    event = ex_ctx.new_event(name="/home", route=ex_ctx.listener.routes[-1])
    assert {event_bob} == event.parents
