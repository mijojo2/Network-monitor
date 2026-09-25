from dataclasses import dataclass, field
from typing import List


@dataclass
class SubDevice:
    name: str
    ip: str
    status: str = "Unknown"
    latency: str = "-"


def get_default_sub_devices(ip: str) -> List[SubDevice]:
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
    status: str = "Unknown"
    latency: str = "-"
    sub_devices: List[SubDevice] = field(default_factory=list)

    def __post_init__(self):
        cleaned = []
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