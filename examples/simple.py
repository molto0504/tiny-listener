"""
:Example:

    >>> tiny-listener simple:app
    Save data done!, username='Alice', age=35
    Send email done!, email='alice@tl.com'
"""

from tiny_listener import Event, Listener


class App(Listener):
    async def listen(self):
        ctx = self.new_ctx()
        ctx.trigger_event("step 2: send email to alice@tl.com")
        ctx.trigger_event("step 1: save Alice's data to database", data={"age": 35})


app = App()


@app.on_event("step 1: save {username}'s data to database")
async def step_1(event: Event):
    username = event.params["username"]
    age = event.data["age"]
    print(f"Save data done!, {username=}, {age=}")


@app.on_event("step 2: send email to {email}", after="step 1*")
async def step_2(event: Event):
    email = event.params["email"]
    print(f"Send email done!, {email=}")
