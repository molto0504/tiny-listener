import asyncio

import pytest

from tiny_listener import Event, Listener, Route


@pytest.fixture()
def route_staff_1():
    return Route(path="/staff_1", fn=lambda: ...)


@pytest.fixture()
def route_staff_2():
    return Route(path="/staff_2", fn=lambda: ...)


@pytest.fixture()
def route_final():
    return Route(path="/final", fn=lambda: ..., parents=["/staff_.*"])


@pytest.fixture()
def app(route_final, route_staff_1, route_staff_2):
    class _App(Listener):
        async def listen(self, *_): ...
    app = _App()
    app.routes = [route_final, route_staff_1, route_staff_2]
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
    assert event.parents == set()
    assert event.is_done is False


def test_parents(app, route_final, route_staff_1, route_staff_2):
    ctx = app.new_ctx("test_parents")
    event_final = Event(name="/final",
                        ctx=ctx,
                        route=route_final)
    event_staff_1 = Event(name="/staff_1",
                          ctx=ctx,
                          route=route_staff_1)
    event_staff_2 = Event(name="/staff_2",
                          ctx=ctx,
                          route=route_staff_2)

    ctx.add_event(event_final)
    assert event_final.parents == set()

    ctx.add_event(event_staff_1)
    assert event_final.parents == {event_staff_1}

    ctx.add_event(event_staff_2)
    assert event_final.parents == {event_staff_1, event_staff_2}


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
