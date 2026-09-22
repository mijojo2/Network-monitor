from dataclasses import dataclass


@dataclass
class Device:
    name: str
    ip: str
    status: str = "Unknown"
    latency: str = "-"