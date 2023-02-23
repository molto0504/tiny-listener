# Tiny "Web Framework"


!!! Info

    **[httptools](https://github.com/MagicStack/httptools)** is a fast HTTP parser lib.


!!! Note

    This tiny "web framework" is just intended to show how tiny-listener works.

    If your really need a web framework for production environment,
    using [FastAPI](https://fastapi.tiangolo.com/) / [Django](https://www.djangoproject.com/) / [Flask](https://flask.palletsprojects.com/) instead.

**STEP 1,** Install Tiny-listener and [httptools](https://github.com/MagicStack/httptools):

```shell
$ pip install tiny-listener httptools 
```

**STEP 2,** Create python file ``http_web.py``:

```python
from asyncio import StreamReader, StreamWriter, start_server

from httptools import HttpRequestParser

from tiny_listener import Event, Listener, EventNotFound

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
    async def handler(self, reader: StreamReader, writer: StreamWriter):
        data = await reader.readuntil(b"\r\n\r\n")
        if data:
            req = Request(data)
            try:
                self.trigger_event(
                    f"{req.method}:{req.url}", data={"writer": writer, "request": req}
                )
            except EventNotFound:
                writer.write(b"HTTP/1.1 404\n\nPage Not Found")
                writer.close()

    async def listen(self):
        await start_server(self.handler, port=PORT)
        print(f"INFO:     HTTP server running on on http://127.0.0.1:{PORT}")


app = App()


@app.after_event
async def response(event: Event):
    writer = event.data["writer"]
    req = event.data["request"]
    writer.write(f"HTTP/1.1 200\n\n{event.result}".encode())
    writer.close()
    print(
        'INFO:     {}:{} - "{} {} HTTP/{}" 200 OK'.format(
            *writer.get_extra_info("peername"), req.method, req.url, req.http_version
        )
    )


@app.on_event("GET:/")
async def home():
    return "Welcome!"


@app.on_event("GET:/user/{username}")
async def hello(event: Event):
    username = event.params["username"]
    return f"Hello, {username}!"
```

**STEP 3,** Run your app:

```shell
$ tiny-listener http_web:app
$ INFO:     Tiny-listener HTTP server running on on localhost:8000
```

**STEP 4,** Try this on your browser: [http://127.0.0.1:8000/user/Bob](http://127.0.0.1:8000/user/Bob)

```shell
...
$ INFO:     127.0.0.1:52579 - "GET /user/Bob HTTP/1.1" 200 OK
```