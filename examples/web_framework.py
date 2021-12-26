"""

1. Install ``httptools``:
```shell
$ pip install httptools
```

Note: ``httptools`` is a parser lib: https://github.com/MagicStack/httptools,
      which may simplify your Application.


2. Run your Application:
```shell
$ tiny-listener web_framework:app
$ INFO:     Tiny-listener HTTP server running on on localhost:8000
```

3. Try this on your browser: http://127.0.0.1:8000/user/Bob
"""

from asyncio import StreamWriter, StreamReader, start_server

from tiny_listener import Event, Listener, RouteNotFound
from httptools import HttpRequestParser


PORT = 8000


class Request:
    def __init__(self, data: bytes):
        self.url = ""
        self.headers = {}
        self.parser = HttpRequestParser(self)
        self.parser.feed_data(data)

    @property
    def method(self) -> str:
        return self.parser.get_method().upper().decode()

    @property
    def http_version(self) -> str:
        return self.parser.get_http_version()

    def on_url(self, url: bytes):
        self.url = url.decode()

    def on_header(self, name, value):
        self.headers[name] = value


class App(Listener):
    async def handler(self, reader: StreamReader, writer: StreamWriter) -> None:
        data = await reader.readuntil(b"\r\n\r\n")
        if data:
            req = Request(data)
            try:
                self.fire(f"{req.method}:{req.url}", data={"writer": writer, "request": req})
            except RouteNotFound:
                writer.write(b"HTTP/1.1 404\n\nNot Found")
                writer.close()

    async def listen(self):
        await start_server(self.handler, host="0.0.0.0", port=PORT)
        print(f"INFO:     Tiny-listener HTTP server running on on localhost:{PORT}")


app = App()


@app.after_event
async def response(event: Event):
    writer = event.data["writer"]
    req = event.data["request"]
    writer.write(f"HTTP/1.1 200\n\n{event.result}".encode())
    writer.close()
    print('INFO:     {}:{} - "{} {} HTTP/{}" 200 OK'.format(
        *writer.get_extra_info("peername"),
        req.method,
        req.url,
        req.http_version
    ))


@app.on_event("GET:/user/{username}")
async def hello(event: Event):
    username = event.params['username']
    return f"Hello, {username}!"
