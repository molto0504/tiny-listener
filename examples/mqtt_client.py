from hbmqtt.client import MQTTClient
from hbmqtt.mqtt.constants import QOS_0
from hbmqtt.mqtt.publish import PublishPacket

from tiny_listener import Listener, Event, Path


class App(Listener):
    async def listen(self, todo):
        client = MQTTClient()
        await client.connect('mqtt://localhost/')
        await client.subscribe([
            ('/sys/device/#', QOS_0),
        ])
        todo("/send", data={"client": client})

        while True:
            message = await client.deliver_message()
            packet: PublishPacket = message.publish_packet
            todo(packet.variable_header.topic_name, data={"payload": packet.payload})


app = App()


@app.do("/sys/device/{id}/log")
async def fn(event: Event, params: Path):
    payload = event.data["payload"]
    print(f"Log handler: {params['id']} => {payload.data}")


@app.do("/sys/device/{id}/power")
async def fn(event: Event, params: Path):
    payload = event.data["payload"]
    print(f"Power handler: {params['id']} => {payload.data}")


@app.do("/send")
async def fn(event: Event):
    client = event.data["client"]
    await client.publish('/sys/device/001/log', b'LOG info: ...')
    await client.publish('/sys/device/002/log', b'LOG error: ...')
    await client.publish('/sys/device/001/power', b'POWER 20%')
    await client.publish('/sys/device/002/power', b'POWER 30%')

app.run()
