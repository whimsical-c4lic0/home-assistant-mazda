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
client_id = f"publish-mazda"
# username = 'emqx'
# password = 'public'


def connect_mqtt():
    def on_connect(client, userdata, flags, rc, properties):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    # client = mqtt_client.Client(client_id)
    client = mqtt_client.Client(
        client_id=client_id,
        callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2,
    )
    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


async def publish(client, mazda, vehicle_id):
    topic = f"mazda/{vehicle_id}"
    while True:
        status = await mazda.get_vehicle_status(vehicle_id)
        print(status)
        client.publish(f"{topic}/monitor", json.dumps(status), retain=True)
        client.publish(f"{topic}/status", "online", retain=True)

        time.sleep(600)  # 10 minutes


async def main():
    # https://github.com/alanzchen/mymazda-relay/blob/main/app.py#L14
    username = os.getenv("MAZDA_USERNAME")
    password = os.getenv("MAZDA_PASSWORD")
    region = "MNAO"
    vehicle_id = None  # os.getenv("MAZDA_ID")

    mazda = MazdaAPI(username, password, region)

    if vehicle_id is None:
        vehicles = await mazda.get_vehicles()
        vehicle_id = vehicles[0]["id"]

    client = connect_mqtt()
    client.loop_start()

    dev_id = f"mazda-{vehicle_id}"

    sensors = [
        {
            "name": "fuelRemaining",
            "dev_cla": None,
            "units": "%",
            "tpl": "fuelRemainingPercent",
            "sclass": "measurement",
        },
        {
            "name": "fuelDistanceRemaining",
            "dev_cla": "distance",
            "units": "km",
            "tpl": "fuelDistanceRemainingKm",
            "sclass": "measurement",
        },
        {
            "name": "odometer",
            "dev_cla": "distance",
            "units": "km",
            "tpl": "odometerKm",
            "sclass": "total",
        },
        {
            "name": "frontLeftTirePressure",
            "dev_cla": "pressure",
            "units": "psi",
            "tpl": "tirePressure.frontLeftTirePressurePsi",
            "sclass": "measurement",
        },
        {
            "name": "frontRightTirePressure",
            "dev_cla": "pressure",
            "units": "psi",
            "tpl": "tirePressure.frontRightTirePressurePsi",
            "sclass": "measurement",
        },
        {
            "name": "rearLeftTirePressure",
            "dev_cla": "pressure",
            "units": "psi",
            "tpl": "tirePressure.rearLeftTirePressurePsi",
            "sclass": "measurement",
        },
        {
            "name": "rearRightTirePressure",
            "dev_cla": "pressure",
            "units": "psi",
            "tpl": "tirePressure.rearRightTirePressurePsi",
            "sclass": "measurement",
        },
    ]

    for s in sensors:
        discovery = {
            "name": s["name"],
            "uniq_id": f"{dev_id}-{s['name']}",
            #            "dev_cla":s["dev_cla"],
            "unit_of_measurement": s["units"],
            "~": f"mazda/{vehicle_id}",
            "stat_t": "~/monitor",
            "val_tpl": "{{ value_json." + s.get("tpl", "name") + " }}",
            "object_id": f"mazda-{s['name']}",
            "avty_t": "~/status",
            "pl_avail": "online",
            "pl_not_avail": "offline",
            "state_class": s["sclass"],
            "dev": {
                "identifiers": [dev_id],
                "manufacturer": "MAZDA",
                "model": vehicles[0]["modelName"],
                "name": vehicles[0]["nickname"],
            },
        }
        if (
            s["dev_cla"] is not None
        ):  # only add dev_cla if not None, other discovery won't work
            discovery["dev_cla"] = s["dev_cla"]
        client.publish(
            f"homeassistant/sensor/{dev_id}/{s['name']}/config",
            json.dumps(discovery),
            retain=True,
        )

    await publish(client, mazda, vehicle_id)
    client.loop_stop()

    # Close the session
    await mazda.close()


asyncio.run(main())
