import socket
import subprocess
import os

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
        # Check whether Linux identifies this as a wireless interface
        if os.path.isdir(f"{interface_path}/wireless"):
            return "wifi"

        # Otherwise check the Linux interface type
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
    result = subprocess.run(
        ["ip", "addr", "show", interface],
        capture_output=True,
        text=True
    )

    addresses = []

    for line in result.stdout.splitlines():
        parts = line.split()

        if parts and (parts[0] == "inet" or parts[0] == "inet6"):
            addresses.append(parts[1])

    return addresses

def get_mac_address(interface):
    try:
        with open(f"/sys/class/net/{interface}/address", "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return None

## Routing ##

def get_routes():
    result = subprocess.run(
        ["ip", "route"],
        capture_output=True,
        text=True
    )

    routes = []

    for line in result.stdout.splitlines():
        routes.append(line)

    return routes

def get_default_route():
    routes = get_routes()

    for route in routes:
        if route.startswith("default"):
            return route

    return None
    



print(get_default_route())