import asyncio
from unittest import TestCase
import pytest

from tiny_listener import Context, Listener, Event, NotFound


@pytest.fixture()
def app(event_loop):
    class App(Listener):
        async def listen(self, _): ...

    app = App()
    app.loop = event_loop
    return app


@pytest.mark.asyncio
async def test_do(app):
    @app.do("something")
    async def fn(event: Event):
        assert event.data["_key_"] == "_val_"
        raise ValueError()

    with pytest.raises(ValueError):
        task = app.fire("something", data={"_key_": "_val_"})
        await asyncio.gather(task)


@pytest.mark.asyncio
async def test_pre_post_do(app):
    @app.pre_do
    async def fn(event: Event):
        assert event.data["seq"] == 0
        event.data["seq"] += 1

    @app.do("something")
    async def fn(event: Event):
        assert event.data["seq"] == 1
        event.data["seq"] += 1

    @app.post_do
    async def fn(event: Event):
        assert event.data["seq"] == 2

    task = app.fire("something", data={"seq": 0})
    await asyncio.gather(task)


@pytest.mark.asyncio
async def test_error_raise(app):
    @app.do("something")
    async def fn():
        raise ValueError("something wrong")

    @app.error_raise(ValueError)
    async def fn(event: Event, exc: ValueError):
        assert event.data["_key_"] == "_val_"
        assert isinstance(exc, ValueError)

    task = app.fire("something", data={"_key_": "_val_"})
    await asyncio.gather(task)


@pytest.mark.asyncio
async def test_timeout(app):
    @app.do("step_1")
    async def fn():
        await asyncio.sleep(1)

    @app.do("step_2", parents=["step*"])
    async def fn(): ...

    @app.error_raise(asyncio.TimeoutError)
    async def fn(exc: asyncio.TimeoutError):
        assert isinstance(exc, asyncio.TimeoutError)

    task_1 = app.fire("step_1")
    task_2 = app.fire("step_2", timeout=0.1)
    await asyncio.gather(task_1, task_2)


@pytest.mark.asyncio
async def test_exit(app):
    @app.do("something")
    async def fn(ctx: Context):
        ctx.listener.exit()

    with pytest.raises(asyncio.CancelledError):
        await asyncio.gather(app.fire("something"))


@pytest.mark.asyncio
async def test_not_found(app):
    @app.error_raise(NotFound)
    async def fn(exc: NotFound):
        assert isinstance(exc, NotFound)
    await asyncio.gather(app.fire("_not_exist"))


class TestListener(TestCase):
    def setUp(self) -> None:
        class App(Listener):
            async def listen(self, _): ...

        self.app_cls = App

    def test_new_context(self):
        app = self.app_cls()
        self.assertEqual(Context("Bob"), app.new_context("Bob"))

    def test_exception_handler(self):
        app = self.app_cls()
        app.exception_handler(app.loop, {"exception": ValueError()})
        app.exception_handler(app.loop, {"exception": asyncio.CancelledError()})

    def test_default_do(self):
        @self.app_cls.default_do("_do_")
        async def fn(): ...

        app = self.app_cls()
        assert app.routes[0].path == "_do_"

    def test_default_callback(self):
        @self.app_cls.default_pre_do
        async def _pre_do_(): ...
        @self.app_cls.default_post_do
        async def _post_do_(): ...
        @self.app_cls.default_error_raise(ValueError)
        async def _error_raise_(): ...

        app = self.app_cls()
        assert app._pre_do[0].__name__ == "_pre_do_"
        assert app._post_do[0].__name__ == "_post_do_"

        err_handler, err_type = app._error_raise[0]
        assert err_type is ValueError
        assert err_handler.__name__ == "_error_raise_"
