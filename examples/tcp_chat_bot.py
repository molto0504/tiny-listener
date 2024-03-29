"""
See: https://molto0504.github.io/tiny-listener/usage-tcp-chat-bot/
"""

from asyncio import StreamReader, StreamWriter, start_server

from tiny_listener import Data, Depends, EventNotFound, Listener

ADDRESS = ("127.0.0.1", 12345)


class App(Listener):
    @staticmethod
    async def tcp_handler(reader: StreamReader, writer: StreamWriter):
        while True:
            payload = await reader.readline()
            if not payload:
                break

            try:
                app.trigger_event(payload.strip().decode(), data={"writer": writer})
            except EventNotFound:
                writer.write(b"Huh, go on.\n")

    async def listen(self):
        await start_server(self.tcp_handler, *ADDRESS)


app = App()


async def get_writer(writer: Data):
    return writer


@app.on_event("{_}?")
async def ask(writer: StreamWriter = Depends(get_writer)):
    writer.write(b"I am confused, may be you should google it.\n")


@app.on_event("{_}.")
async def answer(writer: StreamWriter = Depends(get_writer)):
    writer.write(b"Yes, it makes sense to me.\n")
