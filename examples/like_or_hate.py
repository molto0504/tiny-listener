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
        ctx = app.new_ctx()
        ctx.trigger_event("I hate bugs.")
        ctx.trigger_event("I like dogs.")
        ctx.trigger_event("I like winter.")
        ctx.trigger_event("I hate summer.")
        ctx.trigger_event("I like you.")
        ctx.trigger_event("I hate you.")


app = App()


@app.on_event("I like {things}.")
async def like(event: Event):
    print(f"✔ {event.params['things']}")


@app.on_event("I hate {things}.", after=["I like*"])
async def hate(event: Event):
    print(f"✖ {event.params['things']}")
