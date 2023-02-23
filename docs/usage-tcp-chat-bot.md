# TCP Chat Bot


**STEP 1,** Install Tiny-listener:

```shell
$ pip install tiny-listener
```

**STEP 2,** Create python file ``tcp_chat_bot.py``:

```python
from asyncio import StreamReader, StreamWriter, start_server

from tiny_listener import Depends, Event, Listener, EventNotFound

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


async def get_writer(event: Event):
    return event.data["writer"]


@app.on_event("{_}?")
async def _(writer: StreamWriter = Depends(get_writer)):
    writer.write(b"I am confused, may be you should google it.\n")


@app.on_event("{_}.")
async def _(writer: StreamWriter = Depends(get_writer)):
    writer.write(b"Yes, it makes sense to me.\n")
```


**STEP 3,** Run your app:

```shell
$ tiny-listener tcp_chat_bot:app
```

**STEP 4,** Open a new terminal with:

```shell
$ nc -I 60 localhost 12345
```

**STEP 5,** Chat with your bot:

```shell
$ hello!
Huh, go on.

$ who are you?
I am confused, may be you should google it.

$ earth is flat.
Yes, it makes sense to me.
```
