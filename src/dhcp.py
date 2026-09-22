import os
import subprocess

CONFIG_PATH = "/etc/dnsmasq.d/pi-gateway.conf"
LEASE_FILE = "/var/lib/misc/dnsmasq.leases"

_DEFAULT_CONFIG = {
    "interface": "wlan0",
    "address": "192.168.50.1",
    "range_start": "192.168.50.100",
    "range_end": "192.168.50.200",
    "lease_time": "12h",
}


def _run(command):
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )


def get_dhcp_status():
    result = _run(["systemctl", "is-active", "dnsmasq"])
    return result.stdout.strip() or "inactive"


def get_dhcp_config():
    if not os.path.exists(CONFIG_PATH):
        return dict(_DEFAULT_CONFIG)

    config = dict(_DEFAULT_CONFIG)

    with open(CONFIG_PATH, "r", encoding="utf-8", errors="replace") as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)

            if key == "interface":
                config["interface"] = value
            elif key == "dhcp-range":
                parts = value.split(",")
                if len(parts) >= 3:
                    config["range_start"] = parts[0]
                    config["range_end"] = parts[1]
                    config["lease_time"] = parts[2]

    return config


def get_leases():
    leases = []

    if not os.path.exists(LEASE_FILE):
        return leases

    with open(LEASE_FILE, "r", encoding="utf-8", errors="replace") as file:
        for line in file:
            parts = line.split()

            if len(parts) < 4:
                continue

            expiry, mac, address, hostname = parts[:4]

            leases.append({
                "expiry": int(expiry) if expiry.isdigit() else None,
                "mac": mac,
                "ip": address,
                "hostname": hostname if hostname != "*" else None,
            })

    return leases


def get_client_lease(client):
    client = str(client).lower()

    for lease in get_leases():
        if client in {
            lease["mac"].lower(),
            lease["ip"].lower(),
            (lease["hostname"] or "").lower(),
        }:
            return lease

    return None


def get_connected_clients():
    return get_leases()


def get_dhcp_health():
    status = get_dhcp_status()
    config = get_dhcp_config()
    leases = get_leases()

    return {
        "status": status,
        "interface": config["interface"],
        "range": f'{config["range_start"]}-{config["range_end"]}',
        "lease_count": len(leases),
    }


def _write_dnsmasq_config(config):
    content = f"""# PiServer DHCP configuration
interface={config["interface"]}
bind-interfaces
dhcp-authoritative
dhcp-range={config["range_start"]},{config["range_end"]},{config["lease_time"]}
dhcp-option=3,{config["address"]}
dhcp-option=6,{config["address"]}
leasefile-ro
"""

    directory = os.path.dirname(CONFIG_PATH)
    os.makedirs(directory, exist_ok=True)

    with open(CONFIG_PATH, "w", encoding="utf-8") as file:
        file.write(content)


def configure_dhcp(config):
    merged = dict(_DEFAULT_CONFIG)
    merged.update(config or {})

    _write_dnsmasq_config(merged)

    test = _run(["dnsmasq", "--test"])
    if test.returncode != 0:
        return False

    result = _run(["systemctl", "restart", "dnsmasq"])
    return result.returncode == 0
