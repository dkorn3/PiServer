import socket
import subprocess
import os


def _run(command):
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )


## Interface Discovery ##


def get_interfaces():
    return [name for _, name in socket.if_nameindex()]


def get_interface_status(interface):
    try:
        with open(f"/sys/class/net/{interface}/operstate", "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return None


def get_interface_type(interface):
    interface_path = f"/sys/class/net/{interface}"

    try:
        if os.path.isdir(f"{interface_path}/wireless"):
            return "wifi"

        with open(f"{interface_path}/type", "r") as file:
            interface_type = int(file.read().strip())

        if interface_type == 772:
            return "loopback"

        if interface_type == 1:
            return "ethernet"

        return f"unknown ({interface_type})"

    except FileNotFoundError:
        return None


## Address Info ##


def get_ip_addresses(interface):
    result = _run(["ip", "addr", "show", interface])

    addresses = []

    for line in result.stdout.splitlines():
        parts = line.split()

        if parts and parts[0] in ("inet", "inet6"):
            addresses.append(parts[1])

    return addresses


def get_mac_address(interface):
    try:
        with open(f"/sys/class/net/{interface}/address", "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return None


def get_interface_info(interface):
    return {
        "name": interface,
        "status": get_interface_status(interface),
        "type": get_interface_type(interface),
        "addresses": get_ip_addresses(interface),
        "mac": get_mac_address(interface),
    }


def get_all_interface_info():
    return {
        interface: get_interface_info(interface)
        for interface in get_interfaces()
    }


## Routing ##


def get_routes():
    result = _run(["ip", "route"])
    return [line for line in result.stdout.splitlines() if line.strip()]


def get_default_route():
    for route in get_routes():
        if route.startswith("default"):
            return route

    return None


def enable_ipv4_forwarding():
    try:
        with open("/proc/sys/net/ipv4/ip_forward", "w", encoding="utf-8") as file:
            file.write("1\n")
        return True
    except OSError:
        return False


def is_ipv4_forwarding_enabled():
    try:
        with open("/proc/sys/net/ipv4/ip_forward", "r", encoding="utf-8") as file:
            return file.read().strip() == "1"
    except OSError:
        return False


def configure_lan_address(interface, address):
    result = _run(["ip", "addr", "replace", address, "dev", interface])
    return result.returncode == 0


def bring_interface_up(interface):
    result = _run(["ip", "link", "set", interface, "up"])
    return result.returncode == 0


def get_network_status():
    return {
        "interfaces": get_all_interface_info(),
        "default_route": get_default_route(),
        "ipv4_forwarding": is_ipv4_forwarding_enabled(),
    }
