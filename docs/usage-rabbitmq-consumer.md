# RabbitMQ Consumer


!!! Info

    **[RabbitMQ](https://www.rabbitmq.com) ** is an open source message broker.

    **[aio-pika](https://aio-pika.readthedocs.io)** is a wrapper for the aiormq for asyncio and humans.

!!! Note

    This tutorial assumes RabbitMQ is installed and running on localhost on the standard port (5672).

    See: [Downloading and Installing RabbitMQ](https://www.rabbitmq.com/download.html)


**STEP 1,** Install Tiny-listener and [aio-pika](https://aio-pika.readthedocs.io):

```shell
$ pip install tiny-listener aio-pika 
```

**STEP 2,** Create python file ``rabbitmq_consumer.py``:

```python
import asyncio

import aio_pika

from tiny_listener import Event, Listener


class App(Listener):
    def __init__(self):
        super().__init__()
        self.conn = None

    async def listen(self):
        self.conn = await aio_pika.connect_robust("amqp://127.0.0.1/")
        async with self.conn:
            channel = await self.conn.channel()
            queue = await channel.declare_queue("test_queue", auto_delete=True)
            app.trigger_event("/mock_producer", data={"channel": channel})
            async with queue.iterator() as msg_queue:
                async for msg in msg_queue:
                    async with msg.process():
                        app.trigger_event(f"/app/{msg.app_id}/consume", data={"data": msg.body})


app = App()


@app.shutdown
async def shutdown():
    await app.conn.close()


@app.on_event("/mock_producer")
async def produce(event: Event):
    channel = event.data["channel"]
    for i in range(10):
        await channel.default_exchange.publish(aio_pika.Message(body=bytes(i), app_id=str(i)), routing_key="test_queue")
        await asyncio.sleep(1)


@app.on_event("/app/{app_id}/consume")
async def consume(event: Event):
    app_id = event.params["app_id"]
    data = event.data["data"]
    print(f"INFO: App[{app_id}] consume: {data}")
```

**STEP 3,** Run your app:

```shell
$ tiny-listener rabbitmq_consumer:app
```

Output:

```log
INFO: App[0] consume: b''
INFO: App[1] consume: b'\x00'
INFO: App[2] consume: b'\x00\x00'
INFO: App[3] consume: b'\x00\x00\x00'
```
