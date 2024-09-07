from dotenv import load_dotenv
import os

from paho.mqtt import client as mqtt_client
import time
import json

import aiohttp
import asyncio

from pymazda.client import Client as MazdaAPI
from pymazda.exceptions import (
    MazdaAccountLockedException,
    MazdaAPIEncryptionException,
    MazdaAuthenticationException,
    MazdaException,
    MazdaTokenExpiredException,
)

# https://blog.gitguardian.com/how-to-handle-secrets-in-python/
load_dotenv()

# https://www.emqx.com/en/blog/how-to-use-mqtt-in-python
broker = os.getenv("MQTT_BROKER")
port = 1883
# Generate a Client ID with the publish prefix.
client_id = f'publish-mazda'
# username = 'emqx'
# password = 'public'

def connect_mqtt():
    def on_connect(client, userdata, flags, rc, properties):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    #client = mqtt_client.Client(client_id)
    client = mqtt_client.Client(client_id=client_id, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)
    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

async def publish(client, mazda):
    msg_count = 1
    vehicle_id = os.getenv("MAZDA_ID")
    topic = f"mazda/{vehicle_id}"
    while True:
        status = await mazda.get_vehicle_status(vehicle_id)
        print(status)
        msg = status
        result = client.publish(topic, json.dumps(msg))
        # result: [0, 1]
        if result[0] == 0:
            print(f"Send `{msg}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")
        msg_count += 1
        if msg_count > 5:
            break
        time.sleep(300)


async def main():
    # https://github.com/alanzchen/mymazda-relay/blob/main/app.py#L14
    username = os.getenv("MAZDA_USERNAME")
    password = os.getenv("MAZDA_PASSWORD")
    region = "MNAO"
    mazda = MazdaAPI(username, password, region)

    client = connect_mqtt()
    client.loop_start()
    await publish(client, mazda)
    client.loop_stop()

    # Close the session
    await mazda.close()

asyncio.run(main())
