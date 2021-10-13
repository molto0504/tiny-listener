from tiny_listener import Listener


class App(Listener):
    async def listen(self, todo):
        todo("/step/3")
        todo("/step/2")
        todo("/step/1")


app = App()


@app.do("/step/1")
async def do_something():
    print("* step 1 done!")


@app.do("/step/2", parents=["/step/1"])
async def do_something():
    print("* step 2 done!")


@app.do("/step/3", parents=["/step/2"])
async def do_something():
    print("* step 3 done!")


app.run()
