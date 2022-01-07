"""
:Example:

    >>> tiny-listener hello_world:app
    Hello
    World
"""

from tiny_listener import Listener


class App(Listener):
    async def listen(self):
        # TODO fix after feature required independent CTX
        # TODO modify README
        # TODO app.new_ctx update its scope which exist
        ctx = self.new_ctx()
        ctx.fire("say world")
        ctx.fire("say hello")


app = App()


@app.on_event("say hello")
async def _():
    print("Hello")


@app.on_event("say world", after="say hello")
async def _():
    print("World")
