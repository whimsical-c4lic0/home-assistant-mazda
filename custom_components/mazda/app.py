from dotenv import load_dotenv
import os

# from paho.mqtt import client as mqtt_client
import time
import json

from ha_mqtt_discoverable import Settings, sensors, DeviceInfo

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

async def publish(client, mazda, vehicle_id):
    topic = f"mazda/{vehicle_id}"
    while True:
        status = await mazda.get_vehicle_status(vehicle_id)
        print(status)
        result = client.publish(topic, json.dumps(status))
        # result: [0, 1]
        if result[0] != 0:
            print(f"Failed to send message to topic {topic}")

        time.sleep(300) # 5 minutes


async def main():
    # https://github.com/alanzchen/mymazda-relay/blob/main/app.py#L14
    username = os.getenv("MAZDA_USERNAME")
    password = os.getenv("MAZDA_PASSWORD")
    region = "MNAO"
    vehicle_id = None # os.getenv("MAZDA_ID")

    mazda = MazdaAPI(username, password, region)

    if vehicle_id is None:
        vehicles = await mazda.get_vehicles()
        vehicle_id = vehicles[0]["id"]

    mqtt_settings = Settings.MQTT(host=os.getenv("MQTT_BROKER"))

    sensor_list = [
        {"name":"fuelRemainingPercent", "class":"None", "units":"%"},
    ]

    device_info = DeviceInfo(name=vehicles[0]["nickname"], identifiers=f"mazda{vehicle_id}")

    for s in sensor_list:
        sensor_info = sensors.SensorInfo(name=s["name"], device_class=s["class"], unit_of_measurement=s["units"], unique_id=f"mazda{vehicle_id}-{s['name']}", device=device_info)
        settings = Settings(mqtt=mqtt_settings, entity=sensor_info)
        mysensor = sensors.Sensor(settings)

    while True:
        status = await mazda.get_vehicle_status(vehicle_id)
        print(status)
        mysensor.set_state(status.get("fuelRemainingPercent", 0))
        time.sleep(300) # 5 minutes

#    client = connect_mqtt()
#    client.loop_start()
#    await publish(client, mazda, vehicle_id)
#    client.loop_stop()

    # Close the session
    await mazda.close()

asyncio.run(main())
