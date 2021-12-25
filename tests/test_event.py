import asyncio

import pytest

from tiny_listener import Event, Listener, Route


@pytest.fixture(scope="module")
def route_stuff_1():
    return Route(path="/stuff_1", fn=lambda: ...)


@pytest.fixture(scope="module")
def route_stuff_2():
    return Route(path="/stuff_2", fn=lambda: ...)


@pytest.fixture(scope="module")
def route_final():
    return Route(path="/final", fn=lambda: ..., after=["/stuff_.*"])


@pytest.fixture(scope="module")
def app(route_final, route_stuff_1, route_stuff_2):
    class _App(Listener):
        async def listen(self, *_): ...

    app = _App()
    app.routes = [route_final, route_stuff_1, route_stuff_2]
    return app


def test_ok(route_final, app):
    ctx = app.new_ctx("test_ok")
    event = Event(name="/final",
                  ctx=ctx,
                  route=route_final,
                  timeout=10,
                  data={"foo": ...},
                  params={"bar": ...})
    assert event.name == "/final"
    assert event.timeout == 10
    assert event.data == {"foo": ...}
    assert event.params == {"bar": ...}
    assert event.error is None
    assert event.route is route_final
    assert event.ctx is ctx
    assert event.listener is app
    assert event.after == set()
    assert event.is_done is False


def test_after(app, route_final, route_stuff_1, route_stuff_2):
    ctx = app.new_ctx("test_after")
    event_final = Event(name="/final",
                        ctx=ctx,
                        route=route_final)
    event_stuff_1 = Event(name="/stuff_1",
                          ctx=ctx,
                          route=route_stuff_1)
    event_stuff_2 = Event(name="/stuff_2",
                          ctx=ctx,
                          route=route_stuff_2)

    ctx.add_event(event_final)
    assert event_final.after == set()

    ctx.add_event(event_stuff_1)
    assert event_final.after == {event_stuff_1}

    ctx.add_event(event_stuff_2)
    assert event_final.after == {event_stuff_1, event_stuff_2}


@pytest.mark.asyncio
async def test_done(event_loop, app, route_final):
    event = Event(name="", ctx=app.new_ctx("test_done"), route=route_final)
    assert event.is_done is False
    event_loop.call_later(0.1, lambda: event.done())
    await event.wait_until_done()
    assert event.is_done is True


@pytest.mark.asyncio
async def test_timeout(event_loop, app, route_final):
    event = Event(name="/final", ctx=app.new_ctx("test_timeout"), route=route_final)
    assert event.is_done is False
    with pytest.raises(asyncio.futures.TimeoutError):
        await event.wait_until_done(timeout=0.1)
    assert event.is_done is False


@pytest.mark.asyncio
async def test_call(event_loop, app, route_final):
    event = Event(name="/final", ctx=app.new_ctx("test_call"), route=route_final)
    assert await event() is ...
