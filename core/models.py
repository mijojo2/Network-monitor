import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class SubDevice:
    name: str
    ip: str
    status: str = "Unknown"  # "Online", "Offline", "Checking", "Unknown"
    latency: str = "-"
    last_seen: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "ip": self.ip,
            "status": self.status,
            "latency": self.latency,
            "last_seen": self.last_seen
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
    last_seen: Optional[float] = None
    last_check: Optional[float] = None
    offline_since: Optional[float] = None

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
                    latency=item.get("latency", "-"),
                    last_seen=item.get("last_seen")
                ))
        self.sub_devices = cleaned

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "ip": self.ip,
            "last_seen": self.last_seen,
            "last_check": self.last_check,
            "offline_since": self.offline_since,
            "sub_devices": [s.to_dict() for s in self.sub_devices]
        }

    def is_offline_over_5m(self, now: Optional[float] = None) -> bool:
        """
        Returns True if the branch is currently Offline and has been continuously down
        for at least 5 minutes (300 seconds) without any successful online response.
        """
        if self.status != "Offline":
            return False
        if now is None:
            now = time.time()
        ref = self.offline_since if self.offline_since is not None else self.last_seen
        if ref is not None and ref > 0:
            return (now - ref) >= 300
        return False

    def get_last_seen_display(self) -> str:
        """Returns human-readable relative time and clock stamp for connection history (live minutes, no seconds)."""
        if self.status == "Online":
            if self.last_seen:
                t_str = time.strftime("%H:%M", time.localtime(self.last_seen))
                return f"🟢 Responded: {t_str}"
            return "🟢 Responded: Just now"
        else:
            ref = self.offline_since if self.offline_since is not None else self.last_seen
            if not ref:
                return "⚪ Last seen: Not recorded yet"
            diff = time.time() - ref
            t_str = time.strftime("%H:%M", time.localtime(ref))
            if diff < 60:
                return f"🔴 Down: <1 min ({t_str})"
            elif diff < 3600:
                mins = int(diff // 60)
                return f"🔴 Down: {mins} min ({t_str})"
            elif diff < 86400:
                hrs = int(diff // 3600)
                mins = int((diff % 3600) // 60)
                return f"🔴 Down: {hrs}h {mins}m ({t_str})"
            else:
                days = int(diff // 86400)
                hrs = int((diff % 86400) // 3600)
                d_str = time.strftime("%b %d %H:%M", time.localtime(ref))
                return f"🔴 Down: {days}d {hrs}h ({d_str})"

    def get_server_sub_device(self) -> Optional[SubDevice]:
        """Returns the server sub-device (matching name == 'server', case-insensitive)."""
        for sub in self.sub_devices:
            if sub.name.strip().lower() == "server":
                return sub
        return None

    def get_server_ip(self) -> Optional[str]:
        s = self.get_server_sub_device()
        return s.ip if s else None

    def get_server_status(self) -> str:
        s = self.get_server_sub_device()
        return s.status if s else "Unknown"

    def is_server_down(self) -> bool:
        """Returns True if the branch has a server sub-device and its status is Offline."""
        s = self.get_server_sub_device()
        return s is not None and s.status == "Offline"

    def is_server_up(self) -> bool:
        """Returns True if the branch has a server sub-device and its status is Online."""
        s = self.get_server_sub_device()
        return s is not None and s.status == "Online"

    def is_router_up_server_down(self) -> bool:
        """
        Returns True when the branch router is Online, but the internal server is Offline.
        Catches the deceptive outage where the router responds but the data server machine is down.
        """
        return self.status == "Online" and self.is_server_down()

    def get_branch_type(self) -> str:
        """Returns 'CircleK' (server ends in .222) or 'Franchise' (server ends in .2)."""
        s = self.get_server_sub_device()
        if s:
            if s.ip.endswith(".222"):
                return "CircleK"
            elif s.ip.endswith(".2"):
                return "Franchise"
        return "Unknown"

    def get_branch_type_display(self) -> str:
        b_type = self.get_branch_type()
        if b_type == "CircleK":
            return "🏢 Circle K"
        elif b_type == "Franchise":
            return "🤝 Franchise"
        return "Unknown"


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
