import asyncio

from tiny_listener import Listener, Params


class App(Listener):
    async def listen(self, fire):
        idx = 0
        while True:
            line = input(f"{idx}, please enter: ")
            fire(line)
            idx += 1
            await asyncio.sleep(0)


app = App()

lines = []


@app.do("done")
async def something():
    print(" ".join(lines))
    app.exit()


@app.do("{line}")
async def something(param: Params):
    lines.append(param["line"])
