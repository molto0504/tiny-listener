"""
:Example:

    >>> tiny-listener mqtt_client:app
    LOG [2021-12-31 11:40:48.685079] | living_room   | 13 °C
    LOG [2021-12-31 11:40:48.685349] | kitchen       | 15 °C
    LOG [2021-12-31 11:40:51.693860] | living_room   | 16 °C
    LOG [2021-12-31 11:40:51.694122] | kitchen       | 14 °C
    LOG [2021-12-31 11:40:54.697005] | living_room   | 26 °C
    ...
"""

import asyncio
from datetime import datetime
from random import randint

from hbmqtt.client import MQTTClient
from hbmqtt.mqtt.constants import QOS_0
from hbmqtt.mqtt.publish import PublishPacket

from tiny_listener import Depends, Event, Listener


class App(Listener):
    async def listen(self):
        self.fire("/send")
        self.fire("/recv")


app = App()


async def get_client() -> MQTTClient:
    client = MQTTClient()
    await client.connect("mqtt://localhost/")
    await client.subscribe(
        [
            ("/home/#", QOS_0),
        ]
    )
    return client


@app.on_event("/home/{room}/temperature")
async def _(event: Event):
    payload = event.data["payload"]
    print(
        "LOG [{}] | {:<13} | {}".format(
            datetime.now(), event.params["room"], payload.data.decode()
        )
    )


@app.on_event("/send")
async def _(client: MQTTClient = Depends(get_client)):
    while True:
        await client.publish(
            "/home/living_room/temperature", f"{randint(10, 30)} ℃".encode()
        )
        await client.publish(
            "/home/kitchen/temperature", f"{randint(10, 30)} ℃".encode()
        )
        await asyncio.sleep(3)


@app.on_event("/recv")
async def _(client: MQTTClient = Depends(get_client)):
    while True:
        message = await client.deliver_message()
        packet: PublishPacket = message.publish_packet
        app.fire(packet.variable_header.topic_name, data={"payload": packet.payload})
