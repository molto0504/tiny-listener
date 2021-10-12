from tiny_listener import Listener, Context


class App(Listener):
    __todos__ = ["step_1", "step_2", "step_3"]

    async def listen(self, todo):
        todo("step_1", cid="Alice")
        todo("step_3", cid="Bob")
        todo("step_2", cid="Bob")
        todo("step_3", cid="Alice")
        todo("step_1", cid="Bob")
        todo("step_2", cid="Alice")


app = App()


@app.do("step_1")
async def something(ctx: Context):
    print(f"* step_1 | {ctx.cid}")


@app.do("step_2", after=["step_1"])
async def something(ctx: Context):
    print(f"* step_2 | {ctx.cid}")


@app.do("step_3", after=["step_2"])
async def something(ctx: Context):
    print(f"* step_3 | {ctx.cid}")


app.run()
