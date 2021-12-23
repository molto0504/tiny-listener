"""
:Example:

    >>> tiny-listener mqtt_client:app
    Run http server on :8000

try open the link on your browser: http://127.0.0.1:8000/user/1
"""

from asyncio import start_server
from typing import Dict

from tiny_listener import Depends, Event, Listener, RouteNotFound


class App(Listener):
    async def handler(self, req, resp) -> None:
        line = await req.readline()
        if line:
            method, path, *_ = line.decode().split()
            try:
                self.fire(f"{method.upper()}:{path}", data={"resp": resp})
            except RouteNotFound:
                resp.write(b"HTTP/1.1 404\n\nNot Found")
                resp.close()
            finally:
                print(f"REQUEST INFO | {method} | {path}")

    async def listen(self):
        await start_server(self.handler, host="0.0.0.0", port=8000)
        print("Run http server on localhost:8000")


app = App()


async def fake_db_table():
    return {
        "1": "Alice",
        "2": "Bob"
    }


@app.on_event("GET:/user/{user_id}")
async def get_user(event: Event, users: Dict = Depends(fake_db_table)):
    resp = event.data["resp"]
    user_id = event.params['user_id']
    user = users.get(user_id)

    if user:
        resp.write(f"HTTP/1.1 200\n\n{user}".encode())
    else:
        resp.write(f"HTTP/1.1 404\n\nUser `{user_id}` does not exist".encode())
    resp.close()
