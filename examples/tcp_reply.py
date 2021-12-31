import asyncio

from tiny_listener import Listener, Event, ContextNotFound

ADDRESS = ("127.0.0.1", 12345)


class App(Listener):
    async def tcp_handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        while True:
            cid = str(hash(writer.get_extra_info("peername")))
            try:
                ctx = self.get_ctx(cid)
            except ContextNotFound:
                ctx = self.new_ctx(cid, scope={"reader": reader, "writer": writer})

            payload = await reader.readline()
            if not payload:
                break
            ctx.fire("/reply", data={"payload": payload})

    async def listen(self):
        await asyncio.start_server(self.tcp_handler, *ADDRESS)


app = App()


@app.on_event("/reply")
async def _(event: Event):
    writer = event.ctx.scope["writer"]
    payload = event.data["payload"]
    writer.write(payload)
