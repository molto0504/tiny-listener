from asyncio import BaseEventLoop

import pytest

from tiny_listener import Event, Listener, Route


@pytest.fixture
def work_1_route() -> Route:
    async def work_1():
        return

    return Route(name="/work_1", fn=work_1)


@pytest.fixture
def work_2_route() -> Route:
    async def work_2():
        return

    return Route(name="/work_2", fn=work_2)


@pytest.fixture
def work_final_route() -> Route:
    async def final_route():
        return

    return Route(name="/final", fn=final_route, after=["/work_.*"])


@pytest.fixture
def app(work_1_route: Route, work_2_route: Route, work_final_route: Route) -> Listener:
    class App(Listener):
        async def listen(self):
            ...

    app = App()
    app.routes = {
        work_1_route.name: work_1_route,
        work_2_route.name: work_2_route,
        work_final_route.name: work_final_route,
    }
    return app


def test_event(work_1_route: Route, app: Listener):
    ctx = app.new_ctx()
    event = Event(ctx=ctx, route=work_1_route)
    assert event.listener is app
    assert event.error is None
    assert event.route is work_1_route
    assert event.ctx is ctx
    assert len(event.after) == 0
    assert event.is_done is False


def test_after(app: Listener, work_1_route: Route, work_2_route: Route, work_final_route: Route):
    ctx = app.new_ctx()
    event = Event(ctx=ctx, route=work_final_route)
    assert event.listener is app
    assert event.error is None
    assert event.route is work_final_route
    assert event.ctx is ctx
    assert len(event.after) == 2  # todo
    assert event.is_done is False


@pytest.mark.asyncio
async def test_done(event_loop: BaseEventLoop, app: Listener, work_final_route: Route):
    event = Event(ctx=app.new_ctx(), route=work_final_route)
    assert event.is_done is False
    event_loop.call_later(0.1, lambda: event.done())
    await event.wait_until_done()
    assert event.is_done is True


@pytest.mark.asyncio
async def test_prevent_auto_done(app: Listener, work_final_route: Route) -> None:
    event = Event(ctx=app.new_ctx(), route=work_final_route)
    assert event.auto_done is True
    event.prevent_auto_done()
    assert event.auto_done is False


# todo
# @pytest.mark.asyncio
# async def test_timeout(app: Listener, route_final: Route) -> None:
#     event = Event(ctx=app.new_ctx("test_timeout"), route=route_final)
#     assert event.is_done is False
#     with pytest.raises(asyncio.TimeoutError):
#         await event.wait_until_done(timeout=0.1)
#     assert event.is_done is False


# todo
@pytest.mark.asyncio
async def test_call(app: Listener, work_1_route: Route) -> None:
    event = Event(ctx=app.new_ctx(), route=work_1_route)
    await event()
