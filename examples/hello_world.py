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
        ctx.trigger_event("say world")
        ctx.trigger_event("say hello")


app = App()


@app.on_event("say hello")
async def _():
    print("Hello")


@app.on_event("say world", after="say hello")
async def _():
    print("World")
