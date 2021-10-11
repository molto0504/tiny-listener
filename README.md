# Tiny-listener

Tiny-listener is a lightning-fast, high-performance event handle framework with Python 3.6+

## Requirements

Python 3.6+

## Installation

```shell
$ pip3 install tiny-listener
```

## Example

**example.py**

```python
from tiny_listener import Listener, Event


class App(Listener):
    async def listen(self, send):
        send(Event("event.foo"))
        send(Event("event.bar"))
        send(Event("event.baz"))

        
app = App()


@app.do("event.foo")
async def do_something():
    print("Hello foo!")

    
@app.do("event.bar")
async def do_something():
    print("Hello bar!")

    
@app.do("event.baz")
async def do_something():
    print("Hello baz!")
```

Then run the application using tiny-listener command:

```shell
$ tiny-listener example:app
>> Hello foo!
>> Hello bar!
>> Hello baz!
```
