"""
:Example:

    >>> tiny-listener mqtt_client:app
    Run http server on :8080

try open the link on your browser: http://127.0.0.1:8080/user/1
"""


from asyncio import StreamReader, StreamWriter, start_server
from typing import Callable, Dict

from tiny_listener import Listener, Params, Depends, RouteNotFound, Event


class App(Listener):
    async def handler(self, req: StreamReader, resp: StreamWriter) -> None:
        line: bytes = await req.readline()
        if line:
            method, path, *_ = line.decode().split()
            self.fire(f"{method.upper()}:{path}", data={"resp": resp})
            print(f"REQUEST INFO | {method} | {path}")

    async def listen(self, fire: Callable[..., None]):
        await start_server(self.handler, host="0.0.0.0", port=8080)
        print(f"Run http server on :8080")


app = App()

mock_db = {
    "1": "Alice",
    "2": "Bob"
}


async def get_db():
    return mock_db


async def get_resp(event: Event):
    return event.data["resp"]


@app.error_raise(RouteNotFound)
async def api_not_found(*, resp: StreamWriter = Depends(get_resp, use_cache=False)):
    resp.write(b"HTTP/1.1 404\n\nNot Found")
    resp.close()


@app.do("GET:/user/{user_id}")
async def get_user(
        params: Params,
        *,
        db: Dict = Depends(get_db),
        resp: StreamWriter = Depends(get_resp, use_cache=False)
):
    user_id = params['user_id']
    user = db.get(user_id)
    if user:
        resp.write(f"HTTP/1.1 200\n\n{user}".encode())
    else:
        resp.write(f"HTTP/1.1 200\n\nUser `{user_id}` does not exist".encode())
    resp.close()
