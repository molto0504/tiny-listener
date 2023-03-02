"""
Before running this example, you need to install RabbitMQ and start it.

    $ pip install aio-pika

See: https://molto0504.github.io/tiny-listener/usage-rabbitmq-consumer/

:Example:

    >>> tiny-listener rabbitmq_consumer:app
    INFO: App[0] consume: b''
    INFO: App[1] consume: b'\x00'
    INFO: App[2] consume: b'\x00\x00'
    INFO: App[3] consume: b'\x00\x00\x00'
"""

import asyncio

import aio_pika

from tiny_listener import Event, Listener, Param


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
async def consume(event: Event, app_id: Param):
    data = event.data["data"]
    print(f"INFO: App[{app_id}] consume: {data}")
