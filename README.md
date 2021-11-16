# Tiny-listener

Tiny-listener is a lightweight event framework with Python 3.6+

[中文](README-CN.md) / [English](README.md)

## Requirements

Python 3.6+

## Installation

```shell
$ pip install tiny-listener
```

## Feature

Why use tiny-listener:

    - Easy to use
    - High performance

How does tiny-listener work:

    listen(e.g. port, quene, file ...) -> fire(event) -> do(handler)

## Usage

**example.py**

```python
from tiny_listener import Listener, Params

class App(Listener):
    async def listen(self, fire):
        """listen event"""
        fire("Say hi to Alice") # fire event
        fire("Say hi to Bob")
        fire("Say hi to Carol")

        
app = App()


@app.do("Say hi to {name}")
async def say_hi(param: Params):
    """handle event"""
    print("Hi,", param["name"])

```

Run application using tiny-listener command:

```shell
$ tiny-listener example:app
>>> Hi, Alice
>>> Hi, Bob
>>> Hi, Carol
```
