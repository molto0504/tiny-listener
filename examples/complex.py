import asyncio

from tiny_listener import Listener, Context
from concurrent.futures import TimeoutError


class App(Listener):
    async def listen(self, todo):
        todo("step_1", cid="Alice")
        todo("step_3", cid="Bob")
        todo("step_2", cid="Bob", timeout=1)
        todo("step_3", cid="Alice")
        todo("step_1", cid="Bob")
        todo("step_2", cid="Alice")


app = App()


@app.error_raise(TimeoutError)
async def err_handler(err: TimeoutError):
    print(err)


@app.do("step_1")
async def something(ctx: Context):
    print(f"* step_1 | {ctx.cid}")


@app.do("step_2", parents=["step_1"])
async def something(ctx: Context):
    await asyncio.sleep(3)
    print(f"* step_2 | {ctx.cid}")


@app.do("step_3", parents=["step_2"])
async def something(ctx: Context):
    print(f"* step_3 | {ctx.cid}")


app.run()
