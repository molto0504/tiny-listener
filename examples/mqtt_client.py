"""
:Example:

    >>> tiny-listener mqtt_client:app
    Log handler: 001 => bytearray(b'LOG info: ...')
    Log handler: 002 => bytearray(b'LOG error: ...')
    Power handler: 001 => bytearray(b'POWER 20%')
    Power handler: 002 => bytearray(b'POWER 30%')
"""


from hbmqtt.client import MQTTClient
from hbmqtt.mqtt.constants import QOS_0
from hbmqtt.mqtt.publish import PublishPacket

from tiny_listener import Listener, Event


class App(Listener):
    async def listen(self, fire):
        client = MQTTClient()
        await client.connect('mqtt://localhost/')
        await client.subscribe([
            ('/sys/device/#', QOS_0),
        ])
        fire("/send", data={"client": client})
        fire("/recv", data={"client": client})


app = App()


@app.on_event("/sys/device/{id}/log")
async def fn(event: Event):
    payload = event.data["payload"]
    print(f"Log handler: {event.params['id']} => {payload.data}")


@app.on_event("/sys/device/{id}/power")
async def fn(event: Event):
    payload = event.data["payload"]
    print(f"Power handler: {event.params['id']} => {payload.data}")


@app.on_event("/send")
async def fn(event: Event):
    client = event.data["client"]
    await client.publish('/sys/device/001/log', b'LOG info: ...')
    await client.publish('/sys/device/002/log', b'LOG error: ...')
    await client.publish('/sys/device/001/power', b'POWER 20%')
    await client.publish('/sys/device/002/power', b'POWER 30%')


@app.on_event("/recv")
async def fn(event: Event):
    client = event.data["client"]
    while True:
        message = await client.deliver_message()
        packet: PublishPacket = message.publish_packet
        app.fire(packet.variable_header.topic_name, data={"payload": packet.payload})
