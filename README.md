<p align="center">
  <a href="https://molto0504.github.io/tiny-listener"><img src="https://molto0504.github.io/tiny-listener/logo-light.png#only-light" alt="FastAPI"></a>
</p>
<p align="center">
    <em>A lightweight event framework</em>
</p>

<p align="center">
<a href="https://github.com/molto0504/tiny-listener/actions" target="_blank">
    <img src="https://github.com/molto0504/tiny-listener/workflows/Test/badge.svg" alt="Test">
</a>
<a href="https://pypi.org/project/tiny-listener" target="_blank">
    <img src="https://badge.fury.io/py/tiny-listener.svg" alt="Package version">
</a>
<a href="https://pypi.org/project/tiny-listener" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/tiny-listener" alt="Supported Python versions">
</a>
</p>

---

**Documentation**: <a href="https://molto0504.github.io/tiny-listener" target="_blank"> https://molto0504.github.io/tiny-listener </a>

**Source Code**: <a href="https://github.com/molto0504/tiny-listener" target="_blank"> https://github.com/molto0504/tiny-listener </a>


--- 


# Introduction

Tiny-listener is a lightweight and flexible event framework.

## Requirements

Python 3.8+

## Installation

```shell
$ pip install tiny-listener
```

## Why use tiny-listener

- ✔ Pure Python.
- ✔ Lightning-fast, based on native coroutine.
- ✔ 100% test coverage.

## Example

Consider we want to write a program keep listening message received from somewhere (e.g. http request or message queue), when message arrived, we want to execute a series of operations in a certain order, e.g.

- step 1: save user data to database
- step 2: send email to user

In the development process, we often encounter such problems:

- the source of step 1 and step 2 may be different
- step 2 may depend on the result of step 1, that is to say, step 2 may need to wait for step 1 to complete
- there are many messages, many events, and it is not easy to maintain

Tiny-listener may help you solve these problems:


Create a file `example.py` with:

```python
from tiny_listener import Event, Listener, Param


class App(Listener):
    async def listen(self):
        ctx = self.new_ctx()
        ctx.trigger_event("step 2: send email to alice@tl.com")
        ctx.trigger_event("step 1: save Alice's data to database", data={"age": 35})


app = App()


@app.on_event("step 1: save {username}'s data to database")
async def step_1(event: Event, username: Param):
    age = event.data["age"]
    print(f"Step-1: Save data done!, {username=}, {age=}")


@app.on_event("step 2: send email to {email}")
async def step_2(event: Event, email: Param):
    await event.wait_event_done("step_1")
    print(f"Step-2: Send email done!, {email=}")
```

Run it:

```shell
$ tiny-listener example:app
>>> Save data done!, username='Alice', age=35
>>> Send email done!, email='alice@tl.com'
```

## How it works

* Create your own Listener and listen something(e.g. port, queue ...):

```python
from tiny_listener import Event, Listener, Param


class App(Listener):
    async def listen(self):
        ctx = self.new_ctx()
        ctx.trigger_event("step 2: send email to alice@tl.com")
        ctx.trigger_event("step 1: save Alice's data to database", data={"age": 35})
```


* Add event handler to your listener:

```python
app = App()


@app.on_event("step 1: save {username}'s data to database")
async def step_1(event: Event, username: Param):
    age = event.data["age"]
    print(f"Step-1: Save data done!, {username=}, {age=}")


@app.on_event("step 2: send email to {email}")
async def step_2(event: Event, email: Param):
    await event.wait_event_done("step_1")
    print(f"Step-2: Send email done!, {email=}")
```

* Run listener with command:

```shell
$ tiny-listener example:app
```

* Tiny-listener will dispatch every event automatically:

```shell
>>> Step-1: Save data done!, username='Alice', age=35
>>> Step-2: Send email done!, email='alice@tl.com'
```
