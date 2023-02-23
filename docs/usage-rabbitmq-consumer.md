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
import aio_pika

from tiny_listener import Event, Listener


class App(Listener):
    async def listen(self):
        connection = await aio_pika.connect_robust("amqp://127.0.0.1/")
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue("test_queue", auto_delete=True)
            app.trigger_event("/produce", data={"channel": channel})

            async with queue.iterator() as msg_queue:
                async for msg in msg_queue:
                    async with msg.process():
                        app.trigger_event(f"/app/{msg.app_id}/consume", data={"data": msg.body})


app = App()


@app.on_event("/produce")
async def _(event: Event):
    channel = event.data["channel"]
    await channel.default_exchange.publish(
        aio_pika.Message(body=b"Hello, Alice!", app_id="001"), routing_key="test_queue"
    )
    await channel.default_exchange.publish(
        aio_pika.Message(body=b"Hello, Bob!", app_id="002"), routing_key="test_queue"
    )


@app.on_event("/app/{app_id}/consume")
async def _(event: Event):
    app_id = event.params["app_id"]
    data = event.data["data"]
    print("INFO: App[{}] consume: {}".format(app_id, data))
```

**STEP 3,** Run your app:

```shell
$ tiny-listener rabbitmq_consumer:app
```

Check the logs:

```log
INFO: App[001] consume: b'Hello, Alice!'
INFO: App[002] consume: b'Hello, Bob!'
```
