# MQTT Listener

!!! Info

    
    **[MQTT](https://mqtt.org/)** is a lightweight IOT protocol.

    **[amqtt](https://github.com/Yakifo/amqtt)** is an open source MQTT client and broker implementation with asyncio.


!!! Warning

    Most of time, MQTT client requires an available MQTT server.

    We use a publicly test MQTT server [http://test.mosquitto.org/](http://test.mosquitto.org/) here.
    
    Therefore, **please don't publish anything sensitive, anybody could be listening.**


**STEP 1,** Install Tiny-listener and [amqtt](https://github.com/Yakifo/amqtt):

```shell
$ pip install tiny-listener amqtt 
```

**STEP 2,** Create python file ``mqtt_client.py``:

```python
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
```

**STEP 3,** Run your client:

```shell
$ tiny-listener my_mqtt_client:app
```

And check the log:

```log
INFO: living_room   13 °C
INFO: kitchen       15 °C
...
```
