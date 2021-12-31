"""
See: https://molto0504.github.io/tiny-listener/mqtt-listener/
"""

import asyncio
from random import randint

from amqtt.client import MQTTClient
from amqtt.mqtt.constants import QOS_0
from amqtt.mqtt.publish import PublishPacket

from tiny_listener import Depends, Event, Listener

SERVER_ADDRESS = "mqtt://test.mosquitto.org"


class App(Listener):
    async def listen(self):
        self.fire("/send")
        self.fire("/recv")


app = App()


async def get_client() -> MQTTClient:
    client = MQTTClient()
    await client.connect(SERVER_ADDRESS)
    await client.subscribe(
        [
            ("/test/home/+/temperature", QOS_0),
        ]
    )
    return client


@app.on_event("/test/home/{room}/temperature")
async def _(event: Event):
    payload = event.data["payload"]
    print("INFO: {:<13} | {}".format(event.params["room"], payload.data.decode()))


@app.on_event("/send")
async def _(client: MQTTClient = Depends(get_client)):
    while True:
        await client.publish(
            "/test/home/living_room/temperature", f"{randint(10, 30)} ℃".encode()
        )
        await client.publish(
            "/test/home/kitchen/temperature", f"{randint(10, 30)} ℃".encode()
        )
        await asyncio.sleep(3)


@app.on_event("/recv")
async def _(client: MQTTClient = Depends(get_client)):
    while True:
        message = await client.deliver_message()
        packet: PublishPacket = message.publish_packet
        app.fire(packet.variable_header.topic_name, data={"payload": packet.payload})
