import subprocess
import platform
import re
import socket
import struct
import threading
import time
from typing import Tuple, List

IS_WINDOWS = platform.system() == "Windows"
_native_icmp_available = False

if IS_WINDOWS:
    try:
        import ctypes
        from ctypes import wintypes

        iphlpapi = ctypes.windll.iphlpapi

        class IP_OPTION_INFORMATION(ctypes.Structure):
            _fields_ = [
                ('Ttl', wintypes.BYTE),
                ('Tos', wintypes.BYTE),
                ('Flags', wintypes.BYTE),
                ('OptionsSize', wintypes.BYTE),
                ('OptionsData', ctypes.c_void_p)
            ]

        class ICMP_ECHO_REPLY(ctypes.Structure):
            _fields_ = [
                ('Address', wintypes.DWORD),
                ('Status', wintypes.DWORD),
                ('RoundTripTime', wintypes.DWORD),
                ('DataSize', wintypes.WORD),
                ('Reserved', wintypes.WORD),
                ('Data', ctypes.c_void_p),
                ('Options', IP_OPTION_INFORMATION)
            ]

        _IcmpCreateFile = iphlpapi.IcmpCreateFile
        _IcmpCreateFile.restype = wintypes.HANDLE

        _IcmpCloseHandle = iphlpapi.IcmpCloseHandle
        _IcmpCloseHandle.argtypes = [wintypes.HANDLE]
        _IcmpCloseHandle.restype = wintypes.BOOL

        _IcmpSendEcho = iphlpapi.IcmpSendEcho
        _IcmpSendEcho.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            ctypes.c_void_p,
            wintypes.WORD,
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.DWORD,
            wintypes.DWORD
        ]
        _IcmpSendEcho.restype = wintypes.DWORD

        _native_icmp_available = True
    except Exception:
        _native_icmp_available = False

_thread_local = threading.local()


def _get_thread_icmp_handle():
    if not hasattr(_thread_local, "icmp_handle") or _thread_local.icmp_handle is None:
        try:
            _thread_local.icmp_handle = _IcmpCreateFile()
        except Exception:
            _thread_local.icmp_handle = None
    return _thread_local.icmp_handle


def _native_windows_ping(ip: str, timeout_ms: int = 700) -> Tuple[bool, str]:
    try:
        handle = _get_thread_icmp_handle()
        close_on_finish = False
        if not handle:
            handle = _IcmpCreateFile()
            if not handle:
                return False, "-"
            close_on_finish = True

        dest_ip = struct.unpack("I", socket.inet_aton(ip))[0]
        send_data = b"ping"
        reply_size = ctypes.sizeof(ICMP_ECHO_REPLY) + len(send_data) + 64
        reply_buf = ctypes.create_string_buffer(reply_size)

        ret = _IcmpSendEcho(
            handle,
            dest_ip,
            send_data,
            len(send_data),
            None,
            reply_buf,
            reply_size,
            timeout_ms
        )

        if close_on_finish:
            _IcmpCloseHandle(handle)

        if ret > 0:
            reply = ctypes.cast(reply_buf, ctypes.POINTER(ICMP_ECHO_REPLY)).contents
            if reply.Status == 0:
                rtt = reply.RoundTripTime
                return True, f"{rtt} ms"

        return False, "-"
    except Exception:
        return False, "-"


def single_ping(ip: str, timeout_ms: int = 700) -> Tuple[bool, str]:
    """Single raw ICMP ping without retry."""
    if not ip or not ip.strip():
        return False, "-"

    ip = ip.strip()

    if _native_icmp_available:
        try:
            return _native_windows_ping(ip, timeout_ms)
        except Exception:
            pass

    creationflags = 0
    if IS_WINDOWS:
        command = ["ping", "-n", "1", "-w", str(timeout_ms), ip]
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    else:
        timeout_sec = max(1, timeout_ms // 1000)
        command = ["ping", "-c", "1", "-W", str(timeout_sec), ip]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            creationflags=creationflags
        )
        if result.returncode == 0:
            match = re.search(r"time[=<]\s*([0-9]+)", result.stdout)
            if match:
                latency = match.group(1) + " ms"
                return True, latency
        return False, "-"
    except Exception:
        return False, "-"


def ping(ip: str, timeout_ms: int = 700, retries: int = 1) -> Tuple[bool, str]:
    """
    Robust ping with confirmation retry to eliminate false timeouts & status flapping.
    Fast path: Returns immediately on 1st success.
    Confirmation path: Only if 1st fails does it perform an immediate retry to confirm offline state.
    """
    ok, latency = single_ping(ip, timeout_ms)
    if ok:
        return True, latency

    # If first ping failed, confirm with a fast retry before declaring offline
    for _ in range(retries):
        time.sleep(0.04)  # 40ms jitter buffer
        ok, latency = single_ping(ip, timeout_ms)
        if ok:
            return True, latency

    return False, "-"


def scan_device_hierarchy(router_ip: str, sub_ips: List[str], timeout_ms: int = 700) -> Tuple[Tuple[bool, str], List[Tuple[bool, str]]]:
    """
    Smart Hierarchical Scanner:
    1. Tests the parent router first.
    2. If the router is DEAD, skips pinging child sub-devices (they are guaranteed unreachable).
       This saves 4-5 timeouts per dead branch, speeding up dead branch checks by 80%!
    3. If router is UP, tests the sub-devices.
    """
    router_res = ping(router_ip, timeout_ms=timeout_ms, retries=1)
    router_online, _ = router_res

    if not router_online:
        # Router is down; sub-devices are automatically unreachable
        sub_results = [(False, "-")] * len(sub_ips)
        return router_res, sub_results

    # Router is up; test sub-devices
    sub_results = [ping(s_ip, timeout_ms=timeout_ms, retries=1) for s_ip in sub_ips]
    return router_res, sub_results


class ScannerService:
    def __init__(self, timeout_ms: int = 700):
        self.timeout_ms = timeout_ms

    def ping_ip(self, ip: str) -> Tuple[bool, str]:
        return ping(ip, self.timeout_ms)

    def scan_hierarchy(self, router_ip: str, sub_ips: List[str]):
        return scan_device_hierarchy(router_ip, sub_ips, self.timeout_ms)
