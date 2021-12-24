from unittest import TestCase

import pytest

from tiny_listener import Listener, ContextNotFound, Route, RouteNotFound


class App(Listener):
    async def listen(self):
        pass


class TestListener(TestCase):
    def test_ok(self):
        app = App()
        self.assertEqual(app.ctxs, {})
        self.assertEqual(app.routes, [])

    def test_ctxs(self):
        app = App()
        self.assertEqual(app.ctxs, {})
        # create ctx
        ctx = app.new_ctx("test_ctxs")
        self.assertEqual(app.ctxs, {"test_ctxs": ctx})
        # create ctx already exist
        ctx = app.new_ctx("test_ctxs")
        self.assertEqual(app.ctxs, {"test_ctxs": ctx})
        # get ctx
        self.assertIs(app.get_ctx("test_ctxs"), ctx)
        # get ctx does not exist
        with pytest.raises(ContextNotFound):
            app.get_ctx("_not_exit_")

    def test_match(self):
        app = App()

        route_user_list = Route("/users", fn=lambda: ...)
        route_user_detail = Route("/user/{name}", fn=lambda: ...)
        app.routes = [route_user_detail, route_user_list]

        route, params = app.match_route("/users")
        self.assertIs(route, route_user_list)
        self.assertEqual(params, {})

        route, params = app.match_route("/user/bob")
        self.assertIs(route, route_user_detail)
        self.assertIn("name", params)

        with pytest.raises(RouteNotFound):
            app.match_route("/_not_exist_")

    def test_on_event_callback(self):
        app = App()

        @app.on_event("/foo", after="/...", cfg=...)
        def _(): pass

        self.assertEqual(len(app.routes), 1)
        route = app.routes[0]
        self.assertEqual(route.path, "/foo")
        self.assertEqual(route.opts, {"cfg": ...})
        self.assertEqual(route.after, ["/..."])

    def test_startup_callback(self):
        app = App()
        step = []

        @app.startup
        def step_1():
            step.append(1)

        @app.startup
        async def step_2():
            step.append(2)
            app.exit()

        with pytest.raises(SystemExit):
            app.run()
        self.assertEqual(step, [1, 2])

    def test_shutdown_callback(self):
        app = App()
        step = []

        @app.shutdown
        def step_1():
            step.append(1)

        @app.shutdown
        def step_2():
            step.append(2)

        with pytest.raises(SystemExit):
            app.exit()
        self.assertEqual(step, [1, 2])


@pytest.mark.asyncio
async def test_middleware_callback(event_loop):
    app = App()
    step = []

    @app.before_event
    def step_1():
        step.append(1)

    @app.on_event()
    def step_2():
        step.append(2)

    @app.after_event
    async def step_3():
        step.append(3)

    await app.fire("/go")
    assert step == [1, 2, 3]


@pytest.mark.asyncio
async def test_error_handler(event_loop):
    app = App()
    step = []

    @app.on_event()
    async def step_1():
        step.append(1)
        raise ValueError(...)

    @app.error_handler(ValueError)
    async def step_2():
        step.append(2)

    await app.fire("/go")
    assert step == [1, 2]


@pytest.mark.asyncio
async def test_error_raise(event_loop):
    app = App()

    @app.on_event()
    async def _():
        raise ValueError(...)

    @app.error_handler(KeyError)
    async def _(): ...

    with pytest.raises(ValueError):
        await app.fire("/go")
