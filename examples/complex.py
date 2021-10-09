from tiny_listener import Listener, Event, Context


class App(Listener):
    async def listen(self, send):
        Context("Alice").jobs.add("job.1", "job.2")
        Context("Bob").jobs.add("job.1", "job.2")
        send(Event("step_1", cid="Alice"))
        send(Event("step_3", cid="Bob"))
        send(Event("step_2", cid="Bob"))
        send(Event("step_3", cid="Alice"))
        send(Event("step_1", cid="Bob"))
        send(Event("step_2", cid="Alice"))


app = App()


@app.do("step_1")
async def do_something(ctx: Context):
    print(f"* step_1 | {ctx.cid}")
    ctx.jobs.done("job.1")


@app.do("step_2", must_done=["job.1"])
async def do_something(ctx: Context):
    print(f"* step_2 | {ctx.cid}")
    ctx.jobs.done("job.2")


@app.do("step_3", must_done=["job.2"])
async def do_something(ctx: Context):
    print(f"* step_3 | {ctx.cid}")


app.run()
