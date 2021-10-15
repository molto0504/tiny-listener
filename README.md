# Tiny-listener

Tiny-listener is a lightning-fast, high-performance event handle framework with Python 3.6+

[中文](README-CN.md) / [English](README.md)

## Requirements

Python 3.6+

## Installation

```shell
$ pip3 install tiny-listener
```

## Usage

Why use tiny-listener:

    - complement in a easy way
    - high performance
    - friendly API

How does tiny-listener work:

    listen -> todo -> do

A typical usage:

    listen some kind of message queue, and declare handler for the message received

**example.py**

```python
from tiny_listener import Listener

class App(Listener):
    async def listen(self, todo):
        # Normally, event will received from a message queue, such as Redis or RabbitMQ
        # We omitted these events and commit event directly
        todo("/event/2")
        todo("/event/1")

app = App()

@app.do("/event/1")
async def do_something():
    print("* event 1 done!")

@app.do("/event/2", parents=["/event/1"])
async def do_something():
    print("* event 2 done!")
```

Then run the application using tiny-listener command:

```shell
$ tiny-listener example:app
>> event 1 done!
>> event 2 done!
```

Tiny-listener handle the two event by `todo` method declare order, if you exchange them:

```python
from tiny_listener import Listener

class App(Listener):
    async def listen(self, todo):
        todo("/event/2")
        todo("/event/1")
...
```

Run your code, the event order does not change.

Argument `parents` of Method `app.do` can limit event execute order,
it's means */event/2* always run after */event/1*.

Through todo order is wrong, but the decorator `app.do` always handle event in right order.
