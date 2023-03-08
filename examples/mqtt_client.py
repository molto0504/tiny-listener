"""
Before run this example, you need to install amqtt first:

    $ pip install asyncio-mqtt

See: https://molto0504.github.io/tiny-listener/usage-mqtt-client/

:Example:

    >>> tiny-listener mqtt_client:app
    INFO: bathroom      26 ℃
    INFO: living_room   18 ℃
    INFO: bedroom       20 ℃
"""

import asyncio
import random

from asyncio_mqtt import Client

from tiny_listener import Data, Listener, Param

SERVER_HOST = "test.mosquitto.org"


class App(Listener):
    async def listen(self):
        async with Client(SERVER_HOST) as client:
            await client.subscribe("/iot/home/+/temperature")
            self.trigger_event("/mock_iot_device", data={"client": client})
            async with client.messages() as messages:
                # keep listening mqtt messages and trigger `handle_mqtt_msg` event
                async for msg in messages:
                    ctx = app.new_ctx()
                    ctx.trigger_event(msg.topic.value, data={"payload": msg.payload})


app = App()


@app.on_event("/mock_iot_device")
async def mock_iot_device(client: Data):
    """Mock an IoT device that publishes temperature data"""
    while True:
        room = random.choices(["living_room", "kitchen", "bedroom", "bathroom", "balcony"])[0]
        temperature = random.randint(10, 30)
        await client.publish(f"/iot/home/{room}/temperature", temperature)
        await asyncio.sleep(1)


@app.on_event("/iot/home/{room}/temperature")
async def handle_mqtt_msg(payload: Data, room: Param):
    temperature = payload.decode()
    print("INFO: {:<13} {} ℃".format(room, temperature))
