# MQTT Listener

!!! Info

    
    **[MQTT](https://mqtt.org/)** is a lightweight IOT protocol.

    **[hbmqtt](https://hbmqtt.readthedocs.io/en/latest/)** is an open source MQTT client and broker implementation with asyncio.


!!! Warning

    Most of time, MQTT client requires an available MQTT server.

    We use a publicly test MQTT server [http://test.mosquitto.org/](http://test.mosquitto.org/) here.
    
    Therefore, **please don't publish anything sensitive, anybody could be listening.**


**STEP 1,** Install Tiny-listener and [hbmqtt](https://hbmqtt.readthedocs.io/en/latest/):

```shell
$ pip install tiny-listener hbmqtt 
```

**STEP 2,** Create python file ``mqtt_client.py``:

```python
import asyncio
from datetime import datetime
from random import randint

from hbmqtt.client import MQTTClient
from hbmqtt.mqtt.constants import QOS_0
from hbmqtt.mqtt.publish import PublishPacket

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
    print(
        "LOG [{}] | {:<13} | {}".format(
            datetime.now(), event.params["room"], payload.data.decode()
        )
    )


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
```

**STEP 3,** Run your client:

```shell
$ tiny-listener my_mqtt_client:app
```

And check the log:

```log
LOG [2021-12-31 11:40:48.685079] | living_room   | 13 °C
LOG [2021-12-31 11:40:48.685349] | kitchen       | 15 °C
LOG [2021-12-31 11:40:51.693860] | living_room   | 16 °C
LOG [2021-12-31 11:40:51.694122] | kitchen       | 14 °C
...
```
