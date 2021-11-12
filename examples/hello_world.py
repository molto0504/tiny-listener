"""
:Example:

    >>> tiny-listener hello_world:app
    Hello, World!
"""


from tiny_listener import Listener


class App(Listener):
    async def listen(self, fire):
        fire("say hello")
        fire("say world")


app = App()


@app.do("say hello")
async def f():
    print("Hello", end=", ")


@app.do("say world")
async def f():
    import asyncio
    for t in asyncio.Task.all_tasks():
        print(t.get_name())
    print("World!")

