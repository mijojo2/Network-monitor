import json
import os
from models import Device, SubDevice, get_default_sub_devices

DATA_FILE = "devices.JSON" if os.path.exists("devices.JSON") else "devices.json"


def load_devices():
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        devices = []
        for item in data:
            dev = Device(**item)
            if not dev.sub_devices:
                dev.sub_devices = get_default_sub_devices(dev.ip)
            devices.append(dev)
        return devices

    except Exception as e:
        print(f"Error loading devices: {e}")
        return []



def save_devices(devices):
    data = []

    for d in devices:
        item = {
            "name": d.name,
            "ip": d.ip
        }
        sub_list = getattr(d, "sub_devices", [])
        if sub_list:
            item["sub_devices"] = [
                {
                    "name": s.name,
                    "ip": s.ip
                }
                for s in sub_list
            ]
        data.append(item)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)