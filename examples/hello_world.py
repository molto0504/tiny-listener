"""
:Example:

    >>> tiny-listener hello_world:app
    Hello, World!
"""


from tiny_listener import Listener


class App(Listener):
    async def listen(self):
        self.fire("say hello")
        self.fire("say world")


app = App()


@app.on_event("say hello")
async def _():
    print("Hello", end=", ")


@app.on_event("say world")
async def _():
    print("World!")

