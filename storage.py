import json
import os
from models import Device

DATA_FILE = "devices.json"


def load_devices():

    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)

        return [Device(**device) for device in data]

    except:
        return []


def save_devices(devices):

    data = []

    for d in devices:

        data.append({
            "name": d.name,
            "ip": d.ip
        })

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)