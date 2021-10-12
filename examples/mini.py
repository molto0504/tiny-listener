from tiny_listener import Listener


class App(Listener):
    __todos__ = ["step_1", "step_2", "step_3"]

    async def listen(self, todo):
        todo("step_1")
        todo("step_2")
        todo("step_3")


app = App()


@app.do("step_1")
async def do_something():
    print("* step_1")


@app.do("step_2", after=["step_1"])
async def do_something():
    print("* step_2")


@app.do("step_3")
async def do_something():
    print("* step_3")


app.run()
