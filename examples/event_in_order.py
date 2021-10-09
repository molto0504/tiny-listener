import asyncio

from listener import Listener, Event, Context


class App(Listener):
    async def listen(self, send):
        Context(cid="1").jobs.add("job.1", "job.2")
        send(Event("event.step_3", cid="1"))
        send(Event("event.step_2", cid="1"))
        send(Event("event.step_1", cid="1"))
        await asyncio.sleep(1)


app = App()


@app.event("event.step_1")
async def do_something(ctx: Context):
    print("Step 1!")
    ctx.jobs.done("job.1")


@app.event("event.step_2", must_done=["job.1"])
async def do_something(ctx: Context):
    print("Step 2!")
    ctx.jobs.done("job.2")


@app.event("event.step_3", must_done=["job.2"])
async def do_something(ctx: Context):
    print("Step 3!")
    ctx.jobs.done("job.3")


app.run()
