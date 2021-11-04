"""
:Example:

    >>> tiny-listener mqtt_client:app
    Run http server on :8080

try this:

GET:    http://127.0.0.1:8080/user
POST:   http://127.0.0.1:8080/user/bob/18
GET:    http://127.0.0.1:8080/user/bob
DELETE: http://127.0.0.1:8080/user/bob
"""


import asyncio
import json
from typing import Callable

from tiny_listener import Listener, Event, Params, Depends, NotFound


class App(Listener):
    def __init__(self):
        super().__init__()
        self.req_id = 1

    async def handler(self, req: asyncio.StreamReader, resp: asyncio.StreamWriter) -> None:
        line: bytes = await req.readline()
        if line:
            method, path, *_ = line.decode().split()
            try:
                await self.todo(f"{method.upper()}:{path}", cid=str(self.req_id), block=True, data={"resp": resp})
                print(f"REQUEST INFO | {self.req_id} | {method} | {path}")
                self.req_id += 1
            except NotFound:
                resp.write(b"HTTP/1.1 404\n\nNot Found")
            finally:
                resp.close()

    async def listen(self, todo: Callable[..., None]):
        await asyncio.start_server(self.handler, host="0.0.0.0", port=8080, loop=self.loop)
        print(f"Run http server on :8080")


app = App()

user_db = {}


async def response(event: Event):
    return event.data["resp"]


@app.do("GET:/user")
async def fetch_all(*, resp=Depends(response)):
    text = json.dumps({"users": list(user_db.values())})
    resp.write(f"HTTP/1.1 200\nContent-Type: application/json\n\n{text}".encode())


@app.do("GET:/user/{name}")
async def fetch_one(params: Params, *, resp=Depends(response)):
    user = user_db.get(params['name'])
    if user:
        text = json.dumps(user)
        resp.write(f"HTTP/1.1 200\nContent-Type: application/json\n\n{text}".encode())
    else:
        resp.write(b"HTTP/1.1 404\n\nNot Found")


@app.do("POST:/user/{name}/{age:int}")
async def insert_one(params: Params, *, resp=Depends(response)):
    user_db[params["name"]] = params
    resp.write(b"HTTP/1.1 200\n\nOK")


@app.do("DELETE:/user/{name}")
async def delete_one(params: Params, *, resp=Depends(response)):
    try:
        del user_db[params["name"]]
    except KeyError:
        resp.write(b"HTTP/1.1 404\n\nNot Found")
    else:
        resp.write(b"HTTP/1.1 200\n\nOK")
