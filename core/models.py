from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class SubDevice:
    name: str
    ip: str
    status: str = "Unknown"  # "Online", "Offline", "Checking", "Unknown"
    latency: str = "-"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "ip": self.ip,
            "status": self.status,
            "latency": self.latency
        }


def get_default_sub_devices(ip: str) -> List[SubDevice]:
    """Generates standard branch sub-devices based on branch base IP."""
    parts = ip.strip().split(".")
    if len(parts) == 4:
        base = ".".join(parts[:3])
        return [
            SubDevice(name="Fingerprint", ip=f"{base}.201"),
            SubDevice(name="Cash 1", ip=f"{base}.3"),
            SubDevice(name="Cash 2", ip=f"{base}.4"),
            SubDevice(name="manager", ip=f"{base}.5"),
        ]
    return []


@dataclass
class Device:
    name: str
    ip: str
    status: str = "Unknown"  # "Online", "Offline", "Checking", "Unknown"
    latency: str = "-"
    sub_devices: List[SubDevice] = field(default_factory=list)

    def __post_init__(self):
        cleaned: List[SubDevice] = []
        for item in self.sub_devices:
            if isinstance(item, SubDevice):
                cleaned.append(item)
            elif isinstance(item, dict):
                cleaned.append(SubDevice(
                    name=item.get("name", ""),
                    ip=item.get("ip", ""),
                    status=item.get("status", "Unknown"),
                    latency=item.get("latency", "-")
                ))
        self.sub_devices = cleaned

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "ip": self.ip,
            "sub_devices": [s.to_dict() for s in self.sub_devices]
        }


@dataclass
class NetworkStats:
    total_devices: int = 0
    online_devices: int = 0
    offline_devices: int = 0
    checking_devices: int = 0
    unknown_devices: int = 0
    total_sub_devices: int = 0
    online_sub_devices: int = 0
    offline_sub_devices: int = 0

    @property
    def stability_percentage(self) -> float:
        tested = self.online_devices + self.offline_devices
        if tested == 0:
            return 100.0
        return round((self.online_devices / tested) * 100, 1)
