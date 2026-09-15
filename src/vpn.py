import os
import subprocess

DEFAULT_INTERFACE = "wg0"
DEFAULT_CONFIG = "/etc/wireguard/wg0.conf"


def _run(command):
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )


def get_status(interface=DEFAULT_INTERFACE):
    result = _run(["wg", "show", interface])

    if result.returncode == 0:
        return "active"

    return "inactive"


def start(interface=DEFAULT_INTERFACE):
    result = _run(["wg-quick", "up", interface])

    if result.returncode == 0 or "already exists" in result.stderr:
        return True

    return False


def stop(interface=DEFAULT_INTERFACE):
    result = _run(["wg-quick", "down", interface])

    if result.returncode == 0:
        return True

    if "does not exist" in result.stderr:
        return True

    return False


def restart(interface=DEFAULT_INTERFACE):
    stop(interface)
    return start(interface)


def get_handshakes(interface=DEFAULT_INTERFACE):
    result = _run(
        ["wg", "show", interface, "latest-handshakes"]
    )

    if result.returncode != 0:
        return {}

    output = {}

    for line in result.stdout.splitlines():
        parts = line.split()

        if len(parts) != 2:
            continue

        try:
            output[parts[0]] = int(parts[1])
        except ValueError:
            output[parts[0]] = None

    return output


def get_statistics(interface=DEFAULT_INTERFACE):
    result = _run(
        ["wg", "show", interface, "transfer"]
    )

    if result.returncode != 0:
        return {}

    output = {}

    for line in result.stdout.splitlines():
        parts = line.split()

        if len(parts) != 3:
            continue

        try:
            output[parts[0]] = {
                "bytes_received": int(parts[1]),
                "bytes_sent": int(parts[2]),
            }
        except ValueError:
            continue

    return output


def validate_config(path=DEFAULT_CONFIG):
    if not os.path.exists(path):
        return False

    result = _run(["wg-quick", "strip", path])
    return result.returncode == 0
