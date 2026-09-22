import subprocess
import platform
import re


def ping(ip):

    if platform.system() == "Windows":

        command = [
            "ping",
            "-n",
            "1",
            "-w",
            "1000",
            ip
        ]

    else:

        command = [
            "ping",
            "-c",
            "1",
            ip
        ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:

        match = re.search(r"time[=<]\s*([0-9]+)", result.stdout)

        if match:
            latency = match.group(1) + " ms"
        else:
            latency = "-"

        return True, latency

    return False, "-"