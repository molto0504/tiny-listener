"""
:Example:

    >>> tiny-listener tcp_server:app
    b'Hello, World!'
"""


import asyncio

from tiny_listener import Listener

ADDRESS = ("127.0.0.1", 12345)


class App(Listener):
    async def listen(self, todo):
        todo("run server")
        todo("run client")


app = App()


@app.do("run server")
async def run_server():
    async def handler(reader, _):
        while True:
            print(await reader.read(255))
    await asyncio.start_server(handler, *ADDRESS)


@app.do("run client", parents=["run server"])
async def run_client():
    reader, writer = await asyncio.open_connection(*ADDRESS)
    while True:
        writer.write(b"Hello, World!")
        await asyncio.sleep(1)
