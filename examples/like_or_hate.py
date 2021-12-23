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


from tiny_listener import Listener, Event


class App(Listener):
    async def listen(self, fire):
        fire("I hate bugs.")
        fire("I like dogs.")
        fire("I hate summer.")
        fire("I like winter.")
        fire("I hate you.")
        fire("I like you.")


app = App()


@app.on_event("I like {things}.")
async def like(event: Event):
    print(f"✔ {event.params['things']}")


@app.on_event("I hate {things}.", parents=["I like*"])
async def hate(event: Event):
    print(f"✖ {event.params['things']}")
