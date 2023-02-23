"""
Before running this example, you need to install RabbitMQ and start it.

    $ pip install aio-pika

See: https://molto0504.github.io/tiny-listener/usage-rabbitmq-consumer/
"""

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
async def produce(event: Event):
    channel = event.data["channel"]
    await channel.default_exchange.publish(
        aio_pika.Message(body=b"Hello, Alice!", app_id="001"), routing_key="test_queue"
    )
    await channel.default_exchange.publish(
        aio_pika.Message(body=b"Hello, Bob!", app_id="002"), routing_key="test_queue"
    )


@app.on_event("/app/{app_id}/consume")
async def consume(event: Event):
    app_id = event.params["app_id"]
    data = event.data["data"]
    print(f"INFO: App[{app_id}] consume: {data}")
