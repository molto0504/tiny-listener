from tiny_listener import Listener, Event


class App(Listener):
    async def listen(self, send):
        send(Event("step_1"))
        send(Event("step_2"))
        send(Event("step_3"))


app = App()


@app.do("step_1")
async def do_something():
    print("* step_1")


@app.do("step_2")
async def do_something():
    print("* step_2")


@app.do("step_3")
async def do_something():
    print("* step_3")


app.run()
