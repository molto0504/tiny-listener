import asyncio
import pytest
from unittest import TestCase

from tiny_listener import Listener, ContextNotFound, Route, RouteNotFound
# from tiny_listener import Listener, wrap_hook, Context, Event, Params, Depends, ContextNotFound, RouteNotFound


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

    def test_decorator_on_event(self):
        app = App()

        @app.on_event("/foo", after="/...", cfg=...)
        def _(): pass

        self.assertEqual(len(app.routes), 1)
        route = app.routes[0]
        self.assertEqual(route.path, "/foo")
        self.assertEqual(route.opts, {"cfg": ...})
        self.assertEqual(route.after, ["/..."])

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

    def test_decorator_hooks(self):
        app = App()

        @app.startup
        def _(): ...

        @app.shutdown
        def _(): ...

        @app.before_event
        def _(): ...

        @app.after_event
        def _(): ...

        @app.error_handler(ValueError)
        def _(): ...

        # TODO enh


# @pytest.fixture()
# def app():
#     class App(Listener):
#         async def listen(self, _): ...
#     return App()
#
#
# @pytest.fixture()
# def ctx(app):
#     return Context(listener=app, cid="_ctx_id_", scope={"scope_key": "scope_val"})
#
#
# @pytest.fixture()
# def event(ctx):
#     @ctx.listener.on_event(path="/user/{name}")
#     async def f(): ...
#
#     return ctx.new_event("/event", ctx.listener.routes[0])
#
#
# # @pytest.mark.asyncio
# # async def test_wrap_hook_ok(event_loop, event):
# #     async def f1(e: Event):
# #         assert e is event
# #
# #     async def f2(arg_1, e: Event, arg_2):
# #         assert arg_1 is arg_2 is None
# #         assert e is event
# #
# #     async def f3(arg_1, e: Event, *, arg_2=None):
# #         assert arg_1 is arg_2 is None
# #         assert e is event
# #
# #     async def f4(*, e: Event):
# #         assert e is None
# #
# #     async def f5(e_1: Event, *, e_2: Event):
# #         assert e_1 is event
# #         assert e_2 is None
# #
# #     async def f6(c: Context, e: Event, p: Params):
# #         assert c is event.ctx
# #         assert e is event
# #         assert p == {"_key_": "_val_"}
# #
# #     async def f7(arg_1, c: Context, arg_2, e: Event, p: Params):
# #         assert arg_1 is arg_2 is None
# #         assert c is event.ctx
# #         assert e is event
# #         assert p == {"_key_": "_val_"}
# #
# #     async def f8(c: Context, *, e: Event, p: Params):
# #         assert c is event.ctx
# #         assert e is None
# #         assert p is None
# #
# #     async def get_info(e: Event, c: Context, p: Params):
# #         return e, c, p
# #
# #     async def f9(*, info=Depends(get_info)):
# #         e, c, p = info
# #         assert e is event
# #         assert c is event.ctx
# #         assert p == {"_key_": "_val_"}
# #
# #     async def f10(err: BaseException):
# #         assert isinstance(err, ValueError)
# #
# #     async def f11(err: ValueError):
# #         assert isinstance(err, ValueError)
# #
# #     for hook in [f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11]:
# #         await wrap_hook(hook)(event.ctx, event, Params({"_key_": "_val_"}), ValueError())
# #
# #
# # @pytest.mark.asyncio
# # async def test_wrap_hook_depends_use_cache(event):
# #     times = 0
# #
# #     async def dep():
# #         nonlocal times
# #         times += 1
# #         return ...
# #
# #     async def f(e: Event, *, foo=Depends(dep), bar=Depends(dep)):
# #         assert e is event
# #         assert foo is ...
# #         assert bar is ...
# #
# #     await wrap_hook(f)(event.ctx, event, Params(), None)
# #     assert times == 1
#
#
# def test_new_ctx(app):
#     ctx_1 = app.new_ctx("_ctx_id_")
#     assert ctx_1.cid == "_ctx_id_"
#
#     ctx_2 = app.new_ctx("_ctx_id_")
#     assert ctx_1 is ctx_2
#
#
# def test_get_ctx(app):
#     ctx = app.new_ctx("_ctx_id_")
#     assert ctx is app.get_ctx("_ctx_id_")
#
#     with pytest.raises(ContextNotFound):
#         app.get_ctx("_not_exist_")
#
#
# def test_drop_ctx(app):
#     with pytest.raises(ContextNotFound):
#         app.drop_ctx("_ctx_id_")
#
#     ctx = app.new_ctx("_ctx_id_")
#     assert ctx is app.drop_ctx("_ctx_id_")
#
#     with pytest.raises(ContextNotFound):
#         app.get_ctx("_ctx_id_")
#
#
# def test_hook(app):
#     @app.pre_do
#     async def f(): ...
#     assert len(app._pre_do) == 1
#
#     @app.post_do
#     async def f(): ...
#     assert len(app._post_do) == 1
#
#     @app.error_raise(ValueError)
#     async def f(): ...
#     assert len(app._error_raise) == 1
#     assert app._error_raise[0][1] is ValueError
#
#
# def test_match_route(app):
#     @app.on_event("/root/book")
#     async def f(): ...
#
#     @app.on_event("/root/book/{name}")
#     async def f(): ...
#
#     route, param = app.match_route("/root/book")
#     assert route.path == "/root/book"
#     assert param == {}
#
#     route, param = app.match_route("/root/book/moon")
#     assert route.path == "/root/book/{name}"
#     assert param == {"name": "moon"}
#
#     with pytest.raises(RouteNotFound):
#         app.match_route("/_not_exist_")
#
#
# def test_fire(app):
#     @app.pre_do
#     async def f(event: Event):
#         assert event.data["seq"] == 0
#         event.data["seq"] += 1
#
#     @app.on_event("/something")
#     async def f(event: Event):
#         assert event.data["seq"] == 1
#         event.data["seq"] += 1
#
#     @app.post_do
#     async def f(event: Event):
#         assert event.data["seq"] == 2
#         event.data["seq"] += 1
#         raise ValueError()
#
#     @app.error_raise(BaseException)
#     async def f(event: Event, err: ValueError):
#         assert event.data["seq"] == 3
#         assert isinstance(err, ValueError)
#
#     t = app.fire("/something", data={"seq": 0})
#     asyncio.get_event_loop().run_until_complete(t)
#
#
# @pytest.mark.asyncio
# async def test_raise(event_loop, app):
#     @app.on_event("/something")
#     async def fn():
#         raise ValueError
#
#     with pytest.raises(ValueError):
#         await asyncio.gather(app.fire("/something"))
#
#
# # @pytest.mark.asyncio
# # async def test_exit(event_loop, app):
# #     @app.do("/something")
# #     async def fn(ctx: Context):
# #         ctx.listener.exit()
# #
# #     with pytest.raises(asyncio.CancelledError):
# #         await asyncio.gather(app.fire("/something"))
# #
# #
# # @pytest.mark.asyncio
# # async def test_timeout(event_loop, app):
# #     @app.do("/step/1")
# #     async def f(): await asyncio.sleep(10)
# #
# #     @app.do("/step/2", after=["/step/1"])
# #     async def f(): ...
# #
# #     @app.error_raise(asyncio.TimeoutError)
# #     async def f(ctx: Context, err: asyncio.TimeoutError):
# #         assert isinstance(err, asyncio.TimeoutError)
# #         ctx.listener.exit()
# #
# #     t1 = app.fire("/step/1", timeout=0.3)
# #     t2 = app.fire("/step/2")
# #     with pytest.raises(asyncio.CancelledError):
# #         await asyncio.gather(t1, t2)
