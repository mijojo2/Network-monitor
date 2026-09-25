import subprocess
import platform
import re
import socket
import struct

# Check if running on Windows and prepare native Win32 ICMP
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


def _native_windows_ping(ip: str, timeout_ms: int = 400):
    try:
        handle = _IcmpCreateFile()
        if not handle:
            return False, "-"

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

        if ret > 0:
            reply = ctypes.cast(reply_buf, ctypes.POINTER(ICMP_ECHO_REPLY)).contents
            _IcmpCloseHandle(handle)
            if reply.Status == 0:
                rtt = reply.RoundTripTime
                return True, f"{rtt} ms"
        _IcmpCloseHandle(handle)
        return False, "-"
    except Exception:
        return False, "-"


def ping(ip: str, timeout_ms: int = 400):
    if not ip or not ip.strip():
        return False, "-"

    ip = ip.strip()

    # Fast path: Native Windows ICMP (no process spawning, 100x faster, zero lag)
    if _native_icmp_available:
        try:
            return _native_windows_ping(ip, timeout_ms)
        except Exception:
            pass

    # Fallback path: subprocess ping
    creationflags = 0
    if IS_WINDOWS:
        command = [
            "ping",
            "-n", "1",
            "-w", str(timeout_ms),
            ip
        ]
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    else:
        timeout_sec = max(1, timeout_ms // 1000)
        command = [
            "ping",
            "-c", "1",
            "-W", str(timeout_sec),
            ip
        ]

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