import asyncio
import pytest

from tiny_listener import Context, Listener


@pytest.fixture()
def app():
    class App(Listener):
        async def listen(self, _): ...
    app = App()

    @app.do(path="/user/{name}")
    async def f(): ...

    return app


def test_ctx_ok(app):
    # with ctx
    ctx = Context(listener=app, cid="cid_1", scope={"scope_key": "scope_val"})
    assert ctx.cid == "cid_1"
    assert ctx.listener == app
    assert ctx.scope == {"scope_key": "scope_val"}
    assert ctx.events == {}
    assert ctx.cache.all() == {}
    # without ctx
    ctx = Context(listener=app)
    assert ctx.cid == "__main__"
    assert ctx.listener == app
    assert ctx.scope == {}
    assert ctx.events == {}
    assert ctx.cache.all() == {}


def test_new_event(app):
    ctx = Context(listener=app)
    route = app.routes[0]
    event = ctx.new_event(name="/user/bob", route=route)
    assert event.route is app.routes[0]
    assert event.route is route
    assert event.ctx is ctx


def test_fire(app):
    ctx = Context(listener=app, scope={"scope_key": "scope_val"})
    assert isinstance(ctx.fire("/user/bob"), asyncio.Task)
