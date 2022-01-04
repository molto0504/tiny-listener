"""
See: https://molto0504.github.io/tiny-listener/usage-mqtt-client/
"""

from amqtt.client import MQTTClient
from amqtt.mqtt.constants import QOS_0
from amqtt.mqtt.publish import PublishPacket

from tiny_listener import Event, Listener

SERVER_ADDRESS = "mqtt://test.mosquitto.org"


class App(Listener):
    async def listen(self):
        client = MQTTClient()
        await client.connect(SERVER_ADDRESS)
        await client.subscribe(
            [
                ("/test/home/+/temperature", QOS_0),
            ]
        )
        ctx = self.new_ctx(scope={"client": client})
        ctx.fire("/send")
        ctx.fire("/recv")


app = App()


@app.on_event("/send")
async def _(event: Event):
    client = event.ctx.scope["client"]
    await client.publish("/test/home/living_room/temperature", b"13")
    await client.publish("/test/home/kitchen/temperature", b"15")


@app.on_event("/recv")
async def _(event: Event):
    client = event.ctx.scope["client"]
    while True:
        message = await client.deliver_message()
        packet: PublishPacket = message.publish_packet
        app.fire(packet.variable_header.topic_name, data={"payload": packet.payload})


@app.on_event("/test/home/{room}/temperature")
async def _(event: Event):
    room = event.params["room"]
    temperature = event.data["payload"].data.decode()
    print("INFO: {:<13} {} ℃".format(room, temperature))
