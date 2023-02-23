"""
:Example:

    >>> tiny-listener hello_world:app
    Hello
    World
"""

from tiny_listener import Listener


class App(Listener):
    async def listen(self):
        ctx = self.new_ctx()
        ctx.trigger_event("/my_event/world")
        ctx.trigger_event("/my_event/hello")


app = App()


@app.on_event("/my_event/hello")
async def hello():
    print("Hello")


@app.on_event("/my_event/world", after="/my_event/hello")
async def world():
    print("World")
