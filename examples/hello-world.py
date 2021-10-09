from listener import Listener, Event


class App(Listener):
    async def listen(self, send):
        send(Event("event.foo"))
        send(Event("event.bar"))
        send(Event("event.baz"))


app = App()


@app.event("event.foo")
async def do_something():
    print("Hello foo!")


@app.event("event.bar")
async def do_something():
    print("Hello bar!")


@app.event("event.baz")
async def do_something():
    print("Hello baz!")


app.run()
