import asyncio
import signal
from asyncio import BaseEventLoop

import pytest

from tiny_listener import Event, Listener, Route, depend


@pytest.fixture
def work_1_route() -> Route:
    async def work_1():
        return "work_1_result"

    return Route(path="/work_1", fn=work_1)


@pytest.fixture
def work_2_route() -> Route:
    async def work_2():
        return "work_2_result"

    return Route(path="/work_2", fn=work_2)


@pytest.fixture
def work_final_route() -> Route:
    async def final_route():
        return

    return Route(path="/final", fn=final_route)


@pytest.fixture
def app(work_1_route: Route, work_2_route: Route, work_final_route: Route) -> Listener:
    class App(Listener):
        async def listen(self):
            pass

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
    assert event.is_done is False


@pytest.mark.asyncio
async def test_done(event_loop: BaseEventLoop, app: Listener, work_final_route: Route):
    event = Event(ctx=app.new_ctx(), route=work_final_route)
    assert event.is_done is False
    event_loop.call_later(0.1, lambda: event.done())
    await event.wait_until_done()
    assert event.is_done is True


@pytest.mark.asyncio
async def test_prevent_auto_done(app: Listener, work_final_route: Route):
    event = Event(ctx=app.new_ctx(), route=work_final_route)
    assert event.auto_done is True
    event.prevent_auto_done()
    assert event.auto_done is False


@pytest.mark.asyncio
async def test_call(app: Listener, work_1_route: Route):
    event = Event(ctx=app.new_ctx(), route=work_1_route)
    await event()
    assert event.result == "work_1_result"


@pytest.mark.asyncio
async def test_call_event_with_timeout_Depends():
    class App(Listener):
        async def listen(self):
            pass

    app = App()

    async def get_data():
        return "data"

    @app.on_event()
    async def foo(*, data: str = depend(get_data, timeout=0)):
        return data

    event = Event(ctx=app.new_ctx(), route=app.routes["foo"])
    with pytest.raises(asyncio.TimeoutError):
        assert await event() == "data"


def test_wait_event_done():
    class App(Listener):
        async def listen(self):
            ctx = self.new_ctx()
            ctx.trigger_event("/step_2")
            await asyncio.sleep(0.1)
            ctx.trigger_event("/step_1")

    app = App()

    result = []

    @app.on_event("/step_1")
    async def step_1():
        result.append("step_1_data")
        return "data"

    @app.on_event("/step_2")
    async def step_2(event: Event):
        assert await event.wait_event_done("step_1", timeout=1) == ["data"]
        result.append("step_2_data")
        await app.graceful_shutdown(signal.SIGINT)

    app.run()

    assert result == ["step_1_data", "step_2_data"]
