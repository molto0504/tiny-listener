# Tiny "Web Framework"


!!! Info

    **[h11](https://github.com/python-hyper/h11)** is a pure-Python HTTP/1.1 protocol library


!!! Note

    This tiny "web framework" is very simple, just intended to show how tiny-listener works.

    Don't try to use it to implement a web service from scratch, it's not a good idea.

    If you need a web framework for production, please use [FastAPI](https://fastapi.tiangolo.com/), [Django](https://www.djangoproject.com/), or [Flask](https://flask.palletsprojects.com/)

**STEP 1,** Install tiny-listener and [h11](https://github.com/python-hyper/h11):

```shell
$ pip install tiny-listener h11 
```

**STEP 2,** Create python file ``http_web.py``:

```python
import asyncio
from functools import partial

import h11

from tiny_listener import Context, Event, EventNotFound, Listener, Param

PORT = 8000


class HTTPContext(Context):
    def response(self, status_code: int, data: bytes):
        protocol: H11 = self.scope["protocol"]
        protocol.transport.write(protocol.conn.send(h11.Response(status_code=status_code, headers=[])))
        protocol.transport.write(protocol.conn.send(h11.Data(data=data)))
        protocol.transport.write(protocol.conn.send(h11.EndOfMessage()))
        protocol.conn.start_next_cycle()
        host, port, *_ = protocol.transport.get_extra_info("peername")
        print(f'INFO: {host}:{port} - "{self.scope["method"]} {self.scope["path"]} HTTP/1.1" {status_code}')

    def throw_500(self):
        self.response(500, b"Internal Server Error")


class H11(asyncio.Protocol):
    def __init__(self, listener: Listener):
        self.conn = h11.Connection(h11.SERVER)
        self.transport: asyncio.Transport = None
        self.listener = listener

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data: bytes):
        self.conn.receive_data(data)
        self.handle_event()

    def handle_request(self, req: h11.Request):
        path = req.target.decode()
        method = req.method.decode()
        ctx = self.listener.new_ctx(scope={"protocol": self, "path": path, "method": method})
        try:
            ctx.trigger_event(f"{method}:{path}")
        except EventNotFound:
            ctx.trigger_event("/")

    def handle_event(self):
        request = None
        while True:
            event = self.conn.next_event()
            event_type = type(event)
            if event_type is h11.NEED_DATA:
                break

            if event_type is h11.Request:
                request = event
            elif event_type is h11.EndOfMessage:
                self.handle_request(request)


class App(Listener[HTTPContext]):
    async def listen(self) -> None:
        loop = asyncio.get_event_loop()
        await loop.create_server(partial(H11, self), host="localhost", port=PORT)
        print(f"INFO: HTTP server running on on http://127.0.0.1:{PORT}")


app = App()
app.set_context_cls(HTTPContext)


@app.on_event("GET:/user/{username}")
async def hello(event: Event, username: Param):
    event.ctx.response(200, f"Hello, {username}!".encode())


@app.on_event("GET:/throw")
async def throw(event: Event):
    event.ctx.throw_500()


@app.on_event()
async def home(event: Event):
    event.ctx.response(200, b"Welcome!")
```

**STEP 3,** Run your app:

```shell
$ tiny-listener http_web:app
$ INFO: Tiny-listener HTTP server running on on 127.0.0.1:8000
```

**STEP 4,** Try this on your browser: [http://127.0.0.1:8000/user/bob](http://127.0.0.1:8000/user/bob)

```shell
...
$ INFO: ::1:52579 - "GET /user/bob HTTP/1.1" 200
```