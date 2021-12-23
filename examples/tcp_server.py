"""
:Example:

    >>> tiny-listener tcp_server:app
    b'Hello, World!'
"""


import asyncio

from tiny_listener import Listener

ADDRESS = ("127.0.0.1", 12345)


class App(Listener):
    async def listen(self):
        self.fire("run server")
        self.fire("run client")


app = App()


@app.on_event("run server")
async def _():
    async def handler(reader, _):
        while True:
            print(await reader.read(255))
    await asyncio.start_server(handler, *ADDRESS)


@app.on_event("run client", parents=["run server"])
async def _():
    reader, writer = await asyncio.open_connection(*ADDRESS)
    while True:
        writer.write(b"Hello, World!")
        await asyncio.sleep(1)
