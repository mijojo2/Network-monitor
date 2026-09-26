import subprocess
import threading
import time
import re
from typing import Callable, Optional, Tuple


class HQGatewayService:
    """
    Dedicated sentinel service that continuously monitors the HQ Main Router / Gateway
    (Default: 192.168.1.90) using anti-flapping 3-packet verification.
    """

    def __init__(self, target_ip: str = "192.168.1.90", check_interval: float = 4.0, on_status_change: Optional[Callable[[bool, str], None]] = None):
        self.target_ip = target_ip
        self.check_interval = check_interval
        self.on_status_change = on_status_change
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self.current_online: Optional[bool] = None
        self.current_latency: str = "-"

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()

    def stop(self):
        self.is_running = False

    def ping_once(self) -> Tuple[bool, str]:
        """
        Sends 3 echo packets with 500ms timeout each.
        Considers Gateway ONLINE if at least 1 packet responds (eliminating false drop flicker),
        and OFFLINE only if all 3 packets time out.
        """
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
            cmd = ["ping", "-n", "3", "-w", "500", self.target_ip]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3.5,
                startupinfo=startupinfo
            )
            times = re.findall(r"time\s*[<=]\s*(\d+)\s*ms", proc.stdout, re.IGNORECASE)
            if times:
                avg = sum(int(t) for t in times) // len(times)
                lat_display = "<1 ms" if avg == 0 else f"{avg} ms"
                return True, lat_display
            return False, "-"
        except Exception:
            return False, "-"

    def _monitor_loop(self):
        while self.is_running:
            online, latency = self.ping_once()
            self.current_online = online
            self.current_latency = latency
            if self.on_status_change and self.is_running:
                try:
                    self.on_status_change(online, latency)
                except Exception:
                    pass
            time.sleep(self.check_interval)
