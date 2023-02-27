# MQTT Client

!!! Info

    
    **[MQTT](https://mqtt.org/)** is a lightweight IOT protocol.

    **[asyncio_mqtt](https://github.com/sbtinstruments/asyncio-mqtt)** is an open source MQTT client and broker implementation with asyncio.


!!! Warning

    Most of time, MQTT client requires an available MQTT server.

    We use a publicly test MQTT server [http://test.mosquitto.org/](http://test.mosquitto.org/) here.
    
    **Please don't publish anything sensitive, anybody could be listening.**


**STEP 1,** Install Tiny-listener and [asyncio-mqtt](https://github.com/sbtinstruments/asyncio-mqtt):

```shell
$ pip install tiny-listener asyncio-mqtt
```

**STEP 2,** Create python file ``mqtt_client.py``:

```python
import asyncio
import random

from asyncio_mqtt import Client

from tiny_listener import Event, Listener

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
async def mock_iot_device(event: Event):
    """Mock an IoT device that publishes temperature data"""
    client: Client = event.data["client"]
    while True:
        room = random.choices(["living_room", "kitchen", "bedroom", "bathroom", "balcony"])[0]
        temperature = random.randint(10, 30)
        await client.publish(f"/iot/home/{room}/temperature", temperature)
        await asyncio.sleep(1)


@app.on_event("/iot/home/{room}/temperature")
async def handle_mqtt_msg(event: Event):
    room = event.params["room"]
    temperature = event.data["payload"].decode()
    print("INFO: {:<13} {} ℃".format(room, temperature))
```

**STEP 3,** Run your app:

```shell
$ tiny-listener mqtt_client:app
```

Output:

```log
INFO: living_room   29 ℃
INFO: bedroom       29 ℃
INFO: bathroom      12 ℃
```
