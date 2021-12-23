# Tiny-listener

Tiny-listener is a lightweight event framework with Python 3.6+

[中文](README-CN.md) / [English](README.md)

## Requirements

Python 3.6+

## Installation

```shell
$ pip install tiny-listener
```

## Why use tiny-listener:

- ✔ Pure Python, tiny install pack
- ✔ Lighting-fast, based on native coroutine
- ✔ Easy to use

## How it works:

1. Write your event handler, such as:

```python
@app.on_event("emergency")
def plan_B():
    # do something
    ...

@app.on_event()
def plan_A():
    # do something
    ...
```

2. Keep listening (e.g. port, quene ...) until something happen, such as:

```python
async def listen(self):
   while True:
       msg: str = await queue.get()  # msg may be "emergency" or some other status
       self.fire(msg)  # fire event
```

3. Tiny-listener will dispatch event automatically:

   - Normally, when listener receive a `msg`, `plan_A` will be called by default.
   - If `msg` is `emergency` then `plan_B` will be called instead of `plan_A`.

## Usage

**example.py**

```python
from tiny_listener import Listener, Event

class App(Listener):
    async def listen(self):
        """listen event"""
        self.fire("Say hi to Alice")
        self.fire("Say hi to Bob")
        self.fire("Say hi to Carol")

        
app = App()


@app.on_event("Say hi to {name}")
async def say_hi(event: Event):
    """handle event"""
    print("Hi,", event.params["name"])

```

Run application using tiny-listener command:

```shell
$ tiny-listener example:app
>>> Hi, Alice
>>> Hi, Bob
>>> Hi, Carol
```
