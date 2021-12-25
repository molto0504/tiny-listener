<figure markdown> 
  ![Image title](logo-light.png#only-light)
  ![Image title](logo-dark.png#only-dark)
  <figcaption>A lightweight event framework</figcaption>
</figure>

--- 

# Introduction

Tiny-listener is a lightweight and flexible event framework.

## Requirements

Python 3.6+

## Installation

```shell
$ pip install tiny-listener
```

## Why use tiny-listener

- ✔ Pure Python.
- ✔ Lighting-fast, based on native coroutine.
- ✔ 100% test coverage.

## Example

Create a file `example.py` with:

```python
from tiny_listener import Listener, Event

class App(Listener):
    async def listen(self):
        self.fire("Say hi to Alice")
        self.fire("Say hi to Bob")
        self.fire("Say hi to Carol")

        
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
      self.fire("Say hi to Alice")
      self.fire("Say hi to Bob")
      self.fire("Say hi to Carol")
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
