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

from tiny_listener import Event, Listener


class App(Listener):
    async def listen(self):
        self.fire("I hate bugs.")
        self.fire("I like dogs.")
        self.fire("I hate summer.")
        self.fire("I like winter.")
        self.fire("I hate you.")
        self.fire("I like you.")


app = App()


@app.on_event("I like {things}.")
async def like(event: Event):
    print(f"✔ {event.params['things']}")


@app.on_event("I hate {things}.", after=["I like*"])
async def hate(event: Event):
    print(f"✖ {event.params['things']}")
