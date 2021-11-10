"""
:Example:

    >>> tiny-listener like_or_hate:app
    ✔ dogs
    ✔ winter
    ✔ you
    ✖ bugs
    ✖ summer
    ✖ you
"""


from tiny_listener import Listener, Params


class App(Listener):
    async def listen(self, fire):
        fire("I hate bugs.")
        fire("I like dogs.")
        fire("I hate summer.")
        fire("I like winter.")
        fire("I hate you.")
        fire("I like you.")


app = App()


@app.do("I like {things}.")
async def like(param: Params):
    print(f"✔ {param['things']}")


@app.do("I hate {things}.", parents=["I like*"])
async def hate(param: Params):
    print(f"✖ {param['things']}")
