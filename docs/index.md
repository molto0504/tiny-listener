<figure markdown> 
  ![Image title](logo-light.png#only-light)
  ![Image title](logo-dark.png#only-dark)
  <figcaption>A lightweight event framework</figcaption>
</figure>

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

Create a file `example.py` with:

```python
from tiny_listener import Listener, Event

class App(Listener):
    async def listen(self):
        ctx = self.new_ctx()
        ctx.trigger_event("Say hi to Alice")
        ctx.trigger_event("Say hi to Bob")
        ctx.trigger_event("Say hi to Carol")

        
app = App()


@app.on_event("Say hi to {name}")
async def say_hi(event: Event):
    print("Hi,", event.params["name"])

```

Run it:

```shell
$ tiny-listener example:app
>>> Hi, Alice
>>> Hi, Bob
>>> Hi, Carol
```

## How it works

* Create your own Listener and listen something(e.g. port, queue ...):

```python
from tiny_listener import Listener, Event

class App(Listener):
   async def listen(self):
       ctx = self.new_ctx()
       ctx.trigger_event("Say hi to Alice")
       ctx.trigger_event("Say hi to Bob")
       ctx.trigger_event("Say hi to Carol")
```


* Add event handler to your listener:

```python
app = App()

@app.on_event("Say hi to {name}")
async def say_hi(event: Event):
   print("Hi,", event.params["name"])
```

* Run listener with command:

```shell
$ tiny-listener example:app
```

* Tiny-listener will dispatch every event automatically:

```shell
>>> Hi, Alice
>>> Hi, Bob
>>> Hi, Carol
```
