import json
import os
import shutil
import time
from typing import List
from core.models import Device, SubDevice, get_default_sub_devices


class StorageService:
    """Manages persistent storage with atomic writes and automatic rolling backups."""

    def __init__(self, data_file: str = "devices.JSON", backup_dir: str = "backups"):
        # Support case sensitivity / fallback
        if not os.path.exists(data_file) and os.path.exists("devices.json"):
            self.data_file = "devices.json"
        else:
            self.data_file = data_file

        self.backup_dir = backup_dir
        self._ensure_backup_dir()

    def _ensure_backup_dir(self):
        try:
            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir, exist_ok=True)
        except Exception:
            pass

    def create_backup(self):
        """Creates a timestamped backup of the current data file."""
        if not os.path.exists(self.data_file):
            return

        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f"devices_backup_{timestamp}.json")
            shutil.copy2(self.data_file, backup_path)

            # Keep only the last 7 backups
            backups = sorted([
                os.path.join(self.backup_dir, f)
                for f in os.listdir(self.backup_dir)
                if f.startswith("devices_backup_") and f.endswith(".json")
            ])
            while len(backups) > 7:
                oldest = backups.pop(0)
                try:
                    os.remove(oldest)
                except Exception:
                    pass
        except Exception as e:
            print(f"Warning: Failed to create backup: {e}")

    def load_devices(self) -> List[Device]:
        """Loads devices and their sub-devices from JSON safely."""
        if not os.path.exists(self.data_file):
            return []

        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            devices: List[Device] = []
            for item in data:
                dev = Device(
                    name=item.get("name", ""),
                    ip=item.get("ip", ""),
                    status=item.get("status", "Unknown"),
                    latency=item.get("latency", "-"),
                    last_seen=item.get("last_seen"),
                    last_check=item.get("last_check"),
                    sub_devices=item.get("sub_devices", [])
                )
                if not dev.sub_devices:
                    dev.sub_devices = get_default_sub_devices(dev.ip)
                devices.append(dev)

            # Trigger a clean backup on successful load
            self.create_backup()
            return devices

        except Exception as e:
            print(f"Error loading {self.data_file}: {e}")
            # Try to recover from the latest backup if available
            return self._recover_from_backup()

    def _recover_from_backup(self) -> List[Device]:
        try:
            if not os.path.exists(self.backup_dir):
                return []
            backups = sorted([
                os.path.join(self.backup_dir, f)
                for f in os.listdir(self.backup_dir)
                if f.startswith("devices_backup_") and f.endswith(".json")
            ], reverse=True)

            if backups:
                latest = backups[0]
                print(f"Attempting recovery from backup: {latest}")
                with open(latest, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return [Device(**item) for item in data]
        except Exception as err:
            print(f"Recovery failed: {err}")
        return []

    def save_devices(self, devices: List[Device]):
        """
        Atomically saves devices to JSON by writing to a temporary file first,
        then atomically replacing the target to prevent data corruption.
        """
        temp_file = f"{self.data_file}.tmp"
        try:
            data = [d.to_dict() for d in devices]

            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            # Atomic replace on Windows
            if os.path.exists(self.data_file):
                os.replace(temp_file, self.data_file)
            else:
                os.rename(temp_file, self.data_file)

        except Exception as e:
            print(f"Error saving devices: {e}")
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
