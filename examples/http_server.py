import asyncio
from typing import Callable

from tiny_listener import Listener, Event


class App(Listener):
    async def handler(self, req: asyncio.StreamReader, resp: asyncio.StreamWriter) -> None:
        line: bytes = await req.readline()
        if line:
            _, path, *_ = line.decode().split()
            await self.todo(path, resp=resp, block=True)

    async def listen(self, todo: Callable[..., None]):
        await asyncio.start_server(self.handler, host="0.0.0.0", port=8080, loop=self.loop)
        print(f"Run http server on :8080")


app = App()


@app.do("/")
async def http_api(event: Event):
    resp = event.detail["resp"]
    resp.write(b"HTTP/1.1 200 OK\nContent-Length: 13\n\nHello, world!")
    resp.close()


app.run()
