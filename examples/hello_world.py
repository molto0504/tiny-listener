"""
:Example:

    >>> tiny-listener hello_world:app
    Hello
    World
"""

from tiny_listener import Listener


class App(Listener):
    async def listen(self):
        self.fire("say world")
        self.fire("say hello")


app = App()


@app.on_event("say hello")
async def _():
    print("Hello")


@app.on_event("say world", after="say hello")
async def _():
    print("World")
