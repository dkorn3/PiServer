

from flask import (
    Flask,
    request,
    redirect,
    url_for,
    render_template_string,
    jsonify,
)
from datetime import datetime
import ipaddress
import os
import subprocess
import time

import config as gateway_config
import network as network_backend
import dns as dns_backend
import dhcp as dhcp_backend
import firewall as firewall_backend
import nat as nat_backend
import monitoring
import gateway_logger as gateway_logging


app = Flask(__name__)


# ============================================================
# Boot configuration
# ============================================================

try:
    _BOOT_CONFIG = gateway_config.load_config()
except Exception:
    _BOOT_CONFIG = {}


_NETWORK = _BOOT_CONFIG.get("network", {})
_DNS = _BOOT_CONFIG.get("dns", {})
_DHCP = _BOOT_CONFIG.get("dhcp", {})
_FIREWALL = _BOOT_CONFIG.get("firewall", {})
_VPN = _BOOT_CONFIG.get("vpn", {})


CONFIG = {
    "hostname": _BOOT_CONFIG.get(
        "hostname",
        "PiServer",
    ),

    # WAN
    "interface": _NETWORK.get(
        "wan_interface",
        "eth0",
    ),

    # LAN
    "lan_interface": _NETWORK.get(
        "lan_interface",
        "wlan0",
    ),

    "mode": "gateway",

    "ip_address": _NETWORK.get(
        "lan_address",
        "192.168.50.1/24",
    ).split("/")[0],

    "gateway": "",

    "netmask": "255.255.255.0",

    "dns": (
        _DNS.get(
            "upstream_servers",
            ["1.1.1.1"],
        )[0]
        if _DNS.get("upstream_servers")
        else "1.1.1.1"
    ),

    "dhcp_enabled": _DHCP.get(
        "enabled",
        True,
    ),

    "dns_enabled": _DNS.get(
        "enabled",
        False,
    ),

    "firewall_enabled": _FIREWALL.get(
        "enabled",
        False,
    ),

    "vpn_enabled": _VPN.get(
        "enabled",
        False,
    ),

    "nat_enabled": _NETWORK.get(
        "nat_enabled",
        False,
    ),
}


LOGS = []


# ============================================================
# Utility functions
# ============================================================

def run_command(command):
    """
    Run a Linux command safely and return stdout.
    """

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )

        return result.stdout.strip()

    except Exception:
        return ""


def service_active(service):
    """
    Return True if a systemd service is active.
    """

    result = subprocess.run(
        [
            "systemctl",
            "is-active",
            service,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    return result.returncode == 0


def add_log(message):
    """
    Add an entry to the dashboard activity feed.
    """

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    LOGS.insert(
        0,
        {
            "time": timestamp,
            "message": message,
        },
    )

    if len(LOGS) > 100:
        LOGS.pop()

    try:
        gateway_logging.log_info(message)
    except Exception:
        pass


# ============================================================
# Configuration
# ============================================================

def _current_backend_config():
    """
    Build the backend configuration from GUI settings.
    """

    cfg = gateway_config.load_config()

    cfg["hostname"] = CONFIG["hostname"]

    cfg["network"]["wan_interface"] = (
        CONFIG["interface"]
    )

    cfg["network"]["lan_interface"] = (
        CONFIG["lan_interface"]
    )

    if CONFIG["ip_address"]:

        try:
            prefix = ipaddress.IPv4Network(
                "0.0.0.0/"
                + CONFIG["netmask"]
            ).prefixlen

        except ValueError:
            prefix = 24

        cfg["network"]["lan_address"] = (
            f'{CONFIG["ip_address"]}/{prefix}'
        )

        cfg["network"]["lan_network"] = str(
            ipaddress.ip_interface(
                cfg["network"]["lan_address"]
            ).network
        )

    cfg["network"]["nat_enabled"] = (
        CONFIG["nat_enabled"]
    )

    cfg["dhcp"]["enabled"] = (
        CONFIG["dhcp_enabled"]
    )

    cfg["dns"]["enabled"] = (
        CONFIG["dns_enabled"]
    )

    cfg["firewall"]["enabled"] = (
        CONFIG["firewall_enabled"]
    )

    cfg["vpn"]["enabled"] = (
        CONFIG["vpn_enabled"]
    )

    return cfg


# ============================================================
# NAT
# ============================================================

def configure_nat():

    try:

        if CONFIG["nat_enabled"]:

            status = nat_backend.configure_nat()

            success = status.get(
                "enabled",
                False,
            )

            message = (
                "NAT enabled."
            )

        else:

            nat_backend.disable_nat()

            success = True

            message = (
                "NAT disabled."
            )

        add_log(message)

        return success

    except Exception as exc:

        add_log(
            f"NAT configuration failed: {exc}"
        )

        return False


# ============================================================
# DHCP
# ============================================================

def configure_dhcp():

    cfg = _current_backend_config()

    dhcp_cfg = dict(
        cfg["dhcp"]
    )

    dhcp_cfg["interface"] = (
        cfg["network"]["lan_interface"]
    )

    dhcp_cfg["address"] = (
        cfg["network"]["lan_address"]
        .split("/")[0]
    )

    try:

        if CONFIG["dhcp_enabled"]:

            success = (
                dhcp_backend.configure_dhcp(
                    dhcp_cfg
                )
            )

            message = "DHCP enabled."

        else:

            result = subprocess.run(
                [
                    "systemctl",
                    "stop",
                    "dnsmasq",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            success = (
                result.returncode == 0
            )

            message = "DHCP disabled."

        add_log(message)

        return success

    except Exception as exc:

        add_log(
            f"DHCP configuration failed: {exc}"
        )

        return False


# ============================================================
# DNS
# ============================================================

def configure_dns():

    cfg = _current_backend_config()

    servers = cfg["dns"].get(
        "upstream_servers",
        ["1.1.1.1"],
    )

    try:

        if CONFIG["dns_enabled"]:

            dns_backend.set_upstream_servers(
                servers
            )

            success = True
            message = "DNS enabled."

        else:

            # Do not stop dnsmasq here if DHCP is
            # still enabled.
            success = True
            message = "DNS disabled."

        add_log(message)

        return success

    except Exception as exc:

        add_log(
            f"DNS configuration failed: {exc}"
        )

        return False


# ============================================================
# Firewall
# ============================================================

def configure_firewall():

    cfg = _current_backend_config()

    lan = cfg["network"][
        "lan_interface"
    ]

    wan = cfg["network"][
        "wan_interface"
    ]

    try:

        if CONFIG["firewall_enabled"]:

            firewall_backend.save_ruleset(
                lan,
                wan,
            )

            success = (
                firewall_backend
                .apply_firewall_rules(
                    lan,
                    wan,
                )
            )

            message = "Firewall enabled."

        else:

            success = True

            message = "Firewall disabled."

        add_log(message)

        return success

    except Exception as exc:

        add_log(
            f"Firewall configuration failed: {exc}"
        )

        return False


# ============================================================
# VPN
# ============================================================

def configure_vpn():

    add_log(
        "VPN configuration updated."
    )

    return True


# ============================================================
# System metrics
# ============================================================

def get_cpu_usage():
    """
    Calculate CPU utilization from /proc/stat.
    """

    try:

        def read_cpu():

            with open(
                "/proc/stat",
                "r",
                encoding="utf-8",
            ) as file:

                line = file.readline()

            values = list(
                map(
                    int,
                    line.split()[1:],
                )
            )

            idle = values[3]
            total = sum(values)

            return idle, total

        idle1, total1 = read_cpu()

        time.sleep(0.1)

        idle2, total2 = read_cpu()

        idle_delta = idle2 - idle1
        total_delta = total2 - total1

        if total_delta <= 0:
            return 0

        usage = (
            100
            * (1 - idle_delta / total_delta)
        )

        return round(
            max(0, min(100, usage)),
            1,
        )

    except Exception:
        return 0


def get_memory_usage():

    try:

        values = {}

        with open(
            "/proc/meminfo",
            "r",
            encoding="utf-8",
        ) as file:

            for line in file:

                parts = line.split()

                if len(parts) >= 2:

                    values[
                        parts[0].rstrip(":")
                    ] = int(parts[1])

        total = values.get(
            "MemTotal",
            0,
        )

        available = values.get(
            "MemAvailable",
            0,
        )

        if total == 0:
            return 0

        used = total - available

        return round(
            used / total * 100,
            1,
        )

    except Exception:
        return 0


def get_temperature():

    paths = [
        "/sys/class/thermal/"
        "thermal_zone0/temp",
    ]

    for path in paths:

        try:

            with open(
                path,
                "r",
                encoding="utf-8",
            ) as file:

                value = int(
                    file.read().strip()
                )

            return round(
                value / 1000,
                1,
            )

        except Exception:
            continue

    return None


def get_uptime():

    try:

        with open(
            "/proc/uptime",
            "r",
            encoding="utf-8",
        ) as file:

            seconds = float(
                file.read().split()[0]
            )

        days = int(
            seconds // 86400
        )

        hours = int(
            seconds % 86400 // 3600
        )

        minutes = int(
            seconds % 3600 // 60
        )

        if days:

            return (
                f"{days}d "
                f"{hours}h "
                f"{minutes}m"
            )

        return (
            f"{hours}h "
            f"{minutes}m"
        )

    except Exception:
        return "Unknown"


# ============================================================
# Network traffic
# ============================================================

def get_interface_stats(interface):

    try:

        rx_path = (
            "/sys/class/net/"
            f"{interface}/statistics/rx_bytes"
        )

        tx_path = (
            "/sys/class/net/"
            f"{interface}/statistics/tx_bytes"
        )

        with open(
            rx_path,
            "r",
            encoding="utf-8",
        ) as file:

            rx = int(file.read())

        with open(
            tx_path,
            "r",
            encoding="utf-8",
        ) as file:

            tx = int(file.read())

        return {
            "rx": rx,
            "tx": tx,
        }

    except Exception:

        return {
            "rx": 0,
            "tx": 0,
        }


def format_bytes(value):

    if value < 1024:
        return f"{value} B"

    if value < 1024 ** 2:
        return f"{value / 1024:.1f} KB"

    if value < 1024 ** 3:
        return f"{value / 1024 ** 2:.1f} MB"

    return f"{value / 1024 ** 3:.2f} GB"


# ============================================================
# Connected devices
# ============================================================

def get_dhcp_leases():

    leases = []

    lease_files = [
        "/var/lib/misc/dnsmasq.leases",
        "/var/lib/dnsmasq/dnsmasq.leases",
    ]

    lease_file = None

    for path in lease_files:

        if os.path.exists(path):

            lease_file = path
            break

    if not lease_file:
        return leases

    try:

        with open(
            lease_file,
            "r",
            encoding="utf-8",
        ) as file:

            for line in file:

                parts = line.split()

                if len(parts) < 4:
                    continue

                expiry = parts[0]
                mac = parts[1]
                ip = parts[2]
                hostname = parts[3]

                if hostname == "*":
                    hostname = "Unknown device"

                leases.append(
                    {
                        "expiry": expiry,
                        "mac": mac,
                        "ip": ip,
                        "hostname": hostname,
                        "connected": True,
                    }
                )

    except Exception:
        pass

    return leases


def get_arp_devices():

    devices = []

    output = run_command(
        [
            "ip",
            "neigh",
            "show",
            "dev",
            CONFIG["lan_interface"],
        ]
    )

    for line in output.splitlines():

        parts = line.split()

        if len(parts) < 4:
            continue

        ip = parts[0]

        state = parts[-1]

        mac = ""

        if "lladdr" in parts:

            index = parts.index(
                "lladdr"
            )

            if index + 1 < len(parts):
                mac = parts[index + 1]

        devices.append(
            {
                "ip": ip,
                "mac": mac,
                "state": state,
            }
        )

    return devices


def get_connected_devices():

    leases = get_dhcp_leases()
    arp = get_arp_devices()

    arp_by_ip = {
        item["ip"]: item
        for item in arp
    }

    devices = []

    for lease in leases:

        arp_info = arp_by_ip.get(
            lease["ip"],
            {},
        )

        state = arp_info.get(
            "state",
            "UNKNOWN",
        )

        connected = state not in {
            "FAILED",
            "INCOMPLETE",
        }

        device = dict(lease)

        device["connected"] = connected

        if not device["mac"]:
            device["mac"] = (
                arp_info.get(
                    "mac",
                    "",
                )
            )

        devices.append(device)

    # Add ARP devices not present in DHCP leases.
    known_ips = {
        device["ip"]
        for device in devices
    }

    for item in arp:

        if item["ip"] in known_ips:
            continue

        if item["state"] in {
            "FAILED",
            "INCOMPLETE",
        }:
            continue

        devices.append(
            {
                "expiry": "",
                "mac": item["mac"],
                "ip": item["ip"],
                "hostname": "Unknown device",
                "connected": True,
            }
        )

    return devices


# ============================================================
# Internet connectivity
# ============================================================

def internet_available():

    result = subprocess.run(
        [
            "ping",
            "-c",
            "1",
            "-W",
            "2",
            "1.1.1.1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    return result.returncode == 0


# ============================================================
# Dashboard data
# ============================================================

def get_service_status():

    return {
        "dhcp": service_active(
            "dnsmasq"
        )
        and CONFIG["dhcp_enabled"],

        "dns": (
            CONFIG["dns_enabled"]
        ),

        "nat": (
            nat_backend.get_nat_status()
            .get(
                "enabled",
                False,
            )
        ),

        "firewall": (
            CONFIG["firewall_enabled"]
        ),

        "vpn": (
            CONFIG["vpn_enabled"]
        ),
    }


def get_dashboard_data():

    devices = get_connected_devices()

    wan_stats = get_interface_stats(
        CONFIG["interface"]
    )

    lan_stats = get_interface_stats(
        CONFIG["lan_interface"]
    )

    return {
        "timestamp": datetime.now().isoformat(),

        "system": {
            "cpu": get_cpu_usage(),
            "memory": get_memory_usage(),
            "temperature": get_temperature(),
            "uptime": get_uptime(),
        },

        "network": {
            "wan_interface": CONFIG[
                "interface"
            ],

            "lan_interface": CONFIG[
                "lan_interface"
            ],

            "wan_ip": get_interface_ip(
                CONFIG["interface"]
            ),

            "lan_ip": get_interface_ip(
                CONFIG["lan_interface"]
            ),

            "internet": internet_available(),

            "wan_rx": format_bytes(
                wan_stats["rx"]
            ),

            "wan_tx": format_bytes(
                wan_stats["tx"]
            ),

            "lan_rx": format_bytes(
                lan_stats["rx"]
            ),

            "lan_tx": format_bytes(
                lan_stats["tx"]
            ),
        },

        "devices": devices,

        "services": get_service_status(),

        "logs": LOGS[:10],
    }


def get_interface_ip(interface):

    output = run_command(
        [
            "ip",
            "-4",
            "-o",
            "addr",
            "show",
            interface,
        ]
    )

    for line in output.splitlines():

        parts = line.split()

        if "inet" in parts:

            index = parts.index(
                "inet"
            )

            if index + 1 < len(parts):

                return parts[
                    index + 1
                ].split("/")[0]

    return "N/A"


# ============================================================
# Dashboard
# ============================================================

@app.route("/")
def dashboard():

    data = get_dashboard_data()

    return render_template_string(
        HTML,
        page="dashboard",
        config=CONFIG,
        dashboard=data,
        logs=LOGS,
        health=None,
    )


# ============================================================
# Dashboard API
# ============================================================

@app.route("/api/dashboard")
def dashboard_api():

    return jsonify(
        get_dashboard_data()
    )


# ============================================================
# Network
# ============================================================

@app.route(
    "/network",
    methods=["GET", "POST"],
)
def network():

    if request.method == "POST":

        CONFIG["hostname"] = request.form.get(
            "hostname",
            CONFIG["hostname"],
        )

        CONFIG["interface"] = request.form.get(
            "interface",
            CONFIG["interface"],
        )

        CONFIG["lan_interface"] = request.form.get(
            "lan_interface",
            CONFIG["lan_interface"],
        )

        CONFIG["mode"] = request.form.get(
            "mode",
            CONFIG["mode"],
        )

        CONFIG["ip_address"] = request.form.get(
            "ip_address",
            CONFIG["ip_address"],
        )

        CONFIG["gateway"] = request.form.get(
            "gateway",
            CONFIG["gateway"],
        )

        CONFIG["netmask"] = request.form.get(
            "netmask",
            CONFIG["netmask"],
        )

        CONFIG["dns"] = request.form.get(
            "dns",
            CONFIG["dns"],
        )

        CONFIG["nat_enabled"] = (
            request.form.get(
                "nat_enabled"
            )
            == "on"
        )

        configure_network()

        configure_nat()

        add_log(
            "Network settings saved."
        )

        return redirect(
            url_for("network")
        )

    return render_template_string(
        HTML,
        page="network",
        config=CONFIG,
        dashboard=get_dashboard_data(),
        logs=LOGS,
        health=None,
        network_status=(
            update_network_status()
        ),
    )


# ============================================================
# Save network
# ============================================================

def configure_network():

    try:

        cfg = _current_backend_config()

        gateway_config.save_config(
            cfg
        )

        return True

    except Exception as exc:

        add_log(
            f"Network save failed: {exc}"
        )

        return False


# ============================================================
# DHCP
# ============================================================

@app.route(
    "/dhcp",
    methods=["GET", "POST"],
)
def dhcp():

    if request.method == "POST":

        CONFIG["dhcp_enabled"] = (
            request.form.get(
                "dhcp_enabled"
            )
            == "on"
        )

        configure_dhcp()

        return redirect(
            url_for("dhcp")
        )

    return render_template_string(
        HTML,
        page="dhcp",
        config=CONFIG,
        dashboard=get_dashboard_data(),
        logs=LOGS,
        health=None,
    )


# ============================================================
# DNS
# ============================================================

@app.route(
    "/dns",
    methods=["GET", "POST"],
)
def dns():

    if request.method == "POST":

        CONFIG["dns_enabled"] = (
            request.form.get(
                "dns_enabled"
            )
            == "on"
        )

        configure_dns()

        return redirect(
            url_for("dns")
        )

    return render_template_string(
        HTML,
        page="dns",
        config=CONFIG,
        dashboard=get_dashboard_data(),
        logs=LOGS,
        health=None,
    )


# ============================================================
# Firewall
# ============================================================

@app.route(
    "/firewall",
    methods=["GET", "POST"],
)
def firewall():

    if request.method == "POST":

        CONFIG["firewall_enabled"] = (
            request.form.get(
                "firewall_enabled"
            )
            == "on"
        )

        configure_firewall()

        return redirect(
            url_for("firewall")
        )

    return render_template_string(
        HTML,
        page="firewall",
        config=CONFIG,
        dashboard=get_dashboard_data(),
        logs=LOGS,
        health=None,
    )


# ============================================================
# VPN
# ============================================================

@app.route(
    "/vpn",
    methods=["GET", "POST"],
)
def vpn():

    if request.method == "POST":

        CONFIG["vpn_enabled"] = (
            request.form.get(
                "vpn_enabled"
            )
            == "on"
        )

        configure_vpn()

        return redirect(
            url_for("vpn")
        )

    return render_template_string(
        HTML,
        page="vpn",
        config=CONFIG,
        dashboard=get_dashboard_data(),
        logs=LOGS,
        health=None,
    )


# ============================================================
# Monitoring
# ============================================================

@app.route("/monitoring")
def monitoring_page():

    try:
        health = monitoring.get_gateway_health()
    except Exception as exc:
        health = {
            "error": str(exc)
        }

    return render_template_string(
        HTML,
        page="monitoring",
        config=CONFIG,
        dashboard=get_dashboard_data(),
        logs=LOGS,
        health=health,
    )


@app.route("/api/monitoring")
def monitoring_api():

    try:
        health = monitoring.get_gateway_health()
    except Exception as exc:
        health = {
            "error": str(exc)
        }

    return jsonify(health)


# ============================================================
# Device details
# ============================================================

@app.route("/device/<ip>")
def device_details(ip):

    devices = get_connected_devices()

    device = next(
        (
            item
            for item in devices
            if item["ip"] == ip
        ),
        None,
    )

    if device is None:

        return (
            "Device not found",
            404,
        )

    return render_template_string(
        DEVICE_HTML,
        device=device,
        config=CONFIG,
    )


# ============================================================
# Logs
# ============================================================

@app.route("/logs")
def logs():

    return render_template_string(
        HTML,
        page="logs",
        config=CONFIG,
        dashboard=get_dashboard_data(),
        logs=LOGS,
        health=None,
    )


# ============================================================
# Dashboard HTML
# ============================================================

HTML = r"""
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>PiServer</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
    background: #f4f6f8;
    color: #1f2937;
}

.sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    width: 230px;
    background: #111827;
    color: white;
    padding: 22px 14px;
}

.logo {
    font-size: 23px;
    font-weight: 700;
    padding: 0 12px 25px;
}

.logo span {
    font-size: 12px;
    color: #9ca3af;
    display: block;
    margin-top: 3px;
}

.nav a {
    display: block;
    color: #d1d5db;
    text-decoration: none;
    padding: 11px 12px;
    border-radius: 8px;
    margin-bottom: 4px;
}

.nav a:hover,
.nav a.active {
    background: #374151;
    color: white;
}

.main {
    margin-left: 230px;
    padding: 28px;
}

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 25px;
}

.header h1 {
    margin: 0;
    font-size: 28px;
}

.status {
    padding: 8px 13px;
    border-radius: 20px;
    background: #dcfce7;
    color: #166534;
    font-size: 14px;
    font-weight: 600;
}

.grid {
    display: grid;
    grid-template-columns:
        repeat(4, minmax(0, 1fr));
    gap: 16px;
    margin-bottom: 18px;
}

.card {
    background: white;
    border-radius: 13px;
    padding: 20px;
    box-shadow:
        0 1px 3px rgba(0,0,0,.08);
}

.metric-label {
    color: #6b7280;
    font-size: 13px;
    margin-bottom: 8px;
}

.metric {
    font-size: 28px;
    font-weight: 700;
}

.metric-small {
    font-size: 13px;
    color: #6b7280;
    margin-top: 5px;
}

.two-column {
    display: grid;
    grid-template-columns:
        2fr 1fr;
    gap: 18px;
    margin-bottom: 18px;
}

.section-title {
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 15px;
}

.device {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 13px 0;
    border-bottom: 1px solid #e5e7eb;
}

.device:last-child {
    border-bottom: none;
}

.device-name {
    font-weight: 600;
}

.device-ip {
    color: #6b7280;
    font-size: 13px;
    margin-top: 3px;
}

.device-status {
    font-size: 12px;
    color: #166534;
}

.device-link {
    color: inherit;
    text-decoration: none;
}

.service {
    display: flex;
    justify-content: space-between;
    padding: 12px 0;
    border-bottom: 1px solid #e5e7eb;
}

.service:last-child {
    border-bottom: none;
}

.online {
    color: #16a34a;
    font-weight: 600;
}

.offline {
    color: #dc2626;
    font-weight: 600;
}

.activity {
    padding: 11px 0;
    border-bottom: 1px solid #e5e7eb;
    font-size: 14px;
}

.activity-time {
    color: #9ca3af;
    font-size: 12px;
    margin-right: 8px;
}

.network-box {
    display: grid;
    grid-template-columns:
        repeat(2, 1fr);
    gap: 12px;
}

.network-item {
    background: #f9fafb;
    padding: 13px;
    border-radius: 8px;
}

.network-item strong {
    display: block;
    margin-bottom: 4px;
}

.settings {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.btn {
    border: none;
    border-radius: 8px;
    padding: 10px 15px;
    cursor: pointer;
    background: #111827;
    color: white;
}

.btn:hover {
    background: #374151;
}

@media(max-width: 1000px) {

    .grid {
        grid-template-columns:
            repeat(2, 1fr);
    }

    .two-column {
        grid-template-columns: 1fr;
    }

}

@media(max-width: 700px) {

    .sidebar {
        position: static;
        width: 100%;
    }

    .main {
        margin-left: 0;
        padding: 16px;
    }

    .grid {
        grid-template-columns: 1fr;
    }

}

</style>

</head>


<body>


<div class="sidebar">

    <div class="logo">
        PiServer
        <span>Network Gateway</span>
    </div>

    <div class="nav">

        <a
            href="/"
            class="{{ 'active' if page == 'dashboard' else '' }}"
        >
            Dashboard
        </a>

        <a
            href="/network"
            class="{{ 'active' if page == 'network' else '' }}"
        >
            Network
        </a>

        <a
            href="/dhcp"
            class="{{ 'active' if page == 'dhcp' else '' }}"
        >
            DHCP
        </a>

        <a
            href="/dns"
            class="{{ 'active' if page == 'dns' else '' }}"
        >
            DNS
        </a>

        <a
            href="/firewall"
            class="{{ 'active' if page == 'firewall' else '' }}"
        >
            Firewall
        </a>

        <a
            href="/vpn"
            class="{{ 'active' if page == 'vpn' else '' }}"
        >
            VPN
        </a>

        <a
            href="/monitoring"
            class="{{ 'active' if page == 'monitoring' else '' }}"
        >
            Monitoring
        </a>

        <a
            href="/logs"
            class="{{ 'active' if page == 'logs' else '' }}"
        >
            Logs
        </a>

    </div>

</div>


<div class="main">


{% if page == "dashboard" %}


<div class="header">

    <div>
        <h1>Dashboard</h1>
        <div class="metric-small">
            {{ config.hostname }}
        </div>
    </div>

    <div
        id="gateway-status"
        class="status"
    >
        ● Gateway Online
    </div>

</div>


<!-- System metrics -->

<div class="grid">

    <div class="card">

        <div class="metric-label">
            CPU
        </div>

        <div
            class="metric"
            id="cpu"
        >
            {{ dashboard.system.cpu }}%
        </div>

        <div class="metric-small">
            Processor usage
        </div>

    </div>


    <div class="card">

        <div class="metric-label">
            Memory
        </div>

        <div
            class="metric"
            id="memory"
        >
            {{ dashboard.system.memory }}%
        </div>

        <div class="metric-small">
            RAM utilization
        </div>

    </div>


    <div class="card">

        <div class="metric-label">
            Temperature
        </div>

        <div
            class="metric"
            id="temperature"
        >
            {% if dashboard.system.temperature is not none %}
                {{ dashboard.system.temperature }}°C
            {% else %}
                N/A
            {% endif %}
        </div>

        <div class="metric-small">
            Raspberry Pi CPU
        </div>

    </div>


    <div class="card">

        <div class="metric-label">
            Uptime
        </div>

        <div
            class="metric"
            id="uptime"
            style="font-size:23px"
        >
            {{ dashboard.system.uptime }}
        </div>

        <div class="metric-small">
            System uptime
        </div>

    </div>

</div>


<!-- Network -->

<div class="card">

    <div class="section-title">
        Network
    </div>

    <div class="network-box">

        <div class="network-item">

            <strong>
                Internet
            </strong>

            <span id="internet">

                {% if dashboard.network.internet %}
                    <span class="online">
                        ● Online
                    </span>
                {% else %}
                    <span class="offline">
                        ● Offline
                    </span>
                {% endif %}

            </span>

        </div>


        <div class="network-item">

            <strong>
                WAN
            </strong>

            {{ dashboard.network.wan_ip }}

            <div class="metric-small">
                {{ dashboard.network.wan_interface }}
            </div>

        </div>


        <div class="network-item">

            <strong>
                LAN
            </strong>

            {{ dashboard.network.lan_ip }}

            <div class="metric-small">
                {{ dashboard.network.lan_interface }}
            </div>

        </div>


        <div class="network-item">

            <strong>
                Traffic
            </strong>

            ↓ {{ dashboard.network.wan_rx }}
            &nbsp;
            ↑ {{ dashboard.network.wan_tx }}

        </div>

    </div>

</div>


<br>


<div class="two-column">


<!-- Connected devices -->

<div class="card">

    <div class="section-title">

        Connected Devices

        <span
            id="device-count"
            style="
                float:right;
                font-size:13px;
                color:#6b7280;
            "
        >
            {{ dashboard.devices|length }}
        </span>

    </div>


    <div id="devices">

    {% if dashboard.devices %}

        {% for device in dashboard.devices %}

        <a
            class="device-link"
            href="/device/{{ device.ip }}"
        >

            <div class="device">

                <div>

                    <div class="device-name">
                        {{ device.hostname }}
                    </div>

                    <div class="device-ip">

                        {{ device.ip }}

                        {% if device.mac %}
                            · {{ device.mac }}
                        {% endif %}

                    </div>

                </div>

                <div>

                    {% if device.connected %}

                        <div class="device-status">
                            ● Connected
                        </div>

                    {% else %}

                        <div class="offline">
                            ● Offline
                        </div>

                    {% endif %}

                </div>

            </div>

        </a>

        {% endfor %}

    {% else %}

        <div class="metric-small">
            No connected devices detected.
        </div>

    {% endif %}

    </div>

</div>


<!-- Services -->

<div class="card">

    <div class="section-title">
        Services
    </div>


    <div class="service">

        DHCP

        <span
            id="service-dhcp"
            class="{{ 'online' if dashboard.services.dhcp else 'offline' }}"
        >
            ●
            {{ "ON" if dashboard.services.dhcp else "OFF" }}
        </span>

    </div>


    <div class="service">

        DNS

        <span
            id="service-dns"
            class="{{ 'online' if dashboard.services.dns else 'offline' }}"
        >
            ●
            {{ "ON" if dashboard.services.dns else "OFF" }}
        </span>

    </div>


    <div class="service">

        NAT

        <span
            id="service-nat"
            class="{{ 'online' if dashboard.services.nat else 'offline' }}"
        >
            ●
            {{ "ON" if dashboard.services.nat else "OFF" }}
        </span>

    </div>


    <div class="service">

        Firewall

        <span
            id="service-firewall"
            class="{{ 'online' if dashboard.services.firewall else 'offline' }}"
        >
            ●
            {{ "ON" if dashboard.services.firewall else "OFF" }}
        </span>

    </div>


    <div class="service">

        VPN

        <span
            id="service-vpn"
            class="{{ 'online' if dashboard.services.vpn else 'offline' }}"
        >
            ●
            {{ "ON" if dashboard.services.vpn else "OFF" }}
        </span>

    </div>

</div>

</div>


<!-- Activity -->

<div class="card">

    <div class="section-title">
        Recent Activity
    </div>

    <div id="activity">

    {% if dashboard.logs %}

        {% for log in dashboard.logs %}

        <div class="activity">

            <span class="activity-time">
                {{ log.time }}
            </span>

            {{ log.message }}

        </div>

        {% endfor %}

    {% else %}

        <div class="metric-small">
            No recent activity.
        </div>

    {% endif %}

    </div>

</div>


<script>

function updateDashboard() {

    fetch("/api/dashboard")

        .then(response => response.json())

        .then(data => {

            document.getElementById(
                "cpu"
            ).textContent =
                data.system.cpu + "%";


            document.getElementById(
                "memory"
            ).textContent =
                data.system.memory + "%";


            if (
                data.system.temperature !== null
            ) {

                document.getElementById(
                    "temperature"
                ).textContent =
                    data.system.temperature + "°C";

            }


            document.getElementById(
                "uptime"
            ).textContent =
                data.system.uptime;


            document.getElementById(
                "device-count"
            ).textContent =
                data.devices.length;


            const internet =
                document.getElementById(
                    "internet"
                );


            if (data.network.internet) {

                internet.innerHTML =
                    '<span class="online">● Online</span>';

            } else {

                internet.innerHTML =
                    '<span class="offline">● Offline</span>';

            }


            updateService(
                "service-dhcp",
                data.services.dhcp
            );

            updateService(
                "service-dns",
                data.services.dns
            );

            updateService(
                "service-nat",
                data.services.nat
            );

            updateService(
                "service-firewall",
                data.services.firewall
            );

            updateService(
                "service-vpn",
                data.services.vpn
            );


            updateDevices(
                data.devices
            );

        })

        .catch(() => {

            const status =
                document.getElementById(
                    "gateway-status"
                );

            status.textContent =
                "● Dashboard Error";

            status.style.background =
                "#fee2e2";

            status.style.color =
                "#991b1b";

        });

}


function updateService(
    id,
    enabled
) {

    const element =
        document.getElementById(id);

    element.textContent =
        enabled
            ? "● ON"
            : "● OFF";

    element.className =
        enabled
            ? "online"
            : "offline";

}


function updateDevices(
    devices
) {

    const container =
        document.getElementById(
            "devices"
        );

    if (!devices.length) {

        container.innerHTML =
            '<div class="metric-small">' +
            'No connected devices detected.' +
            '</div>';

        return;

    }


    container.innerHTML =
        devices.map(
            device => {

                const status =
                    device.connected
                        ? '<div class="device-status">● Connected</div>'
                        : '<div class="offline">● Offline</div>';

                return `
                    <a
                        class="device-link"
                        href="/device/${device.ip}"
                    >

                        <div class="device">

                            <div>

                                <div class="device-name">
                                    ${escapeHtml(device.hostname)}
                                </div>

                                <div class="device-ip">
                                    ${escapeHtml(device.ip)}
                                    ${
                                        device.mac
                                            ? " · " +
                                              escapeHtml(device.mac)
                                            : ""
                                    }
                                </div>

                            </div>

                            <div>
                                ${status}
                            </div>

                        </div>

                    </a>
                `;

            }
        ).join("");

}


function escapeHtml(
    value
) {

    const div =
        document.createElement(
            "div"
        );

    div.textContent =
        value;

    return div.innerHTML;

}


setInterval(
    updateDashboard,
    3000
);

</script>


{% else %}


<div class="header">

    <div>
        <h1>
            {{ page|capitalize }}
        </h1>

        <div class="metric-small">
            PiServer Network Gateway
        </div>
    </div>

</div>


<div class="card">

    <div class="section-title">
        {{ page|capitalize }}
    </div>

    <p>
        This PiServer module is available
        from the navigation menu.
    </p>

</div>


{% endif %}


</div>

</body>

</html>
"""


# ============================================================
# Device details HTML
# ============================================================

DEVICE_HTML = r"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>{{ device.hostname }} - PiServer</title>

<style>

body {
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
    background: #f4f6f8;
    margin: 0;
    padding: 30px;
    color: #1f2937;
}

.container {
    max-width: 800px;
    margin: auto;
}

.card {
    background: white;
    border-radius: 14px;
    padding: 25px;
    margin-bottom: 18px;
    box-shadow:
        0 1px 3px rgba(0,0,0,.08);
}

h1 {
    margin-top: 0;
}

.row {
    display: flex;
    justify-content: space-between;
    padding: 13px 0;
    border-bottom: 1px solid #e5e7eb;
}

.row:last-child {
    border-bottom: none;
}

.label {
    color: #6b7280;
}

.online {
    color: #16a34a;
    font-weight: 600;
}

.back {
    display: inline-block;
    margin-bottom: 20px;
    text-decoration: none;
    color: #2563eb;
}

</style>

</head>


<body>

<div class="container">

<a
    class="back"
    href="/"
>
    ← Back to Dashboard
</a>


<div class="card">

    <h1>
        {{ device.hostname }}
    </h1>

    <div class="row">

        <span class="label">
            Status
        </span>

        {% if device.connected %}

            <span class="online">
                ● Connected
            </span>

        {% else %}

            <span>
                Offline
            </span>

        {% endif %}

    </div>


    <div class="row">

        <span class="label">
            IP Address
        </span>

        <strong>
            {{ device.ip }}
        </strong>

    </div>


    <div class="row">

        <span class="label">
            MAC Address
        </span>

        <strong>
            {{ device.mac or "Unknown" }}
        </strong>

    </div>


    <div class="row">

        <span class="label">
            Interface
        </span>

        <strong>
            {{ config.lan_interface }}
        </strong>

    </div>


    <div class="row">

        <span class="label">
            DHCP Lease Expiry
        </span>

        <strong>
            {{ device.expiry or "Unknown" }}
        </strong>

    </div>

</div>


<div class="card">

    <h2>
        Device Metrics
    </h2>

    <p>
        Traffic statistics can be added here by
        collecting per-client counters from nftables,
        conntrack, or interface-level accounting.
    </p>

</div>

</div>

</body>

</html>
"""


# ============================================================
# Main
# ============================================================

def main():

    print(
        "==================================="
    )

    print(
        "PiServer Network Gateway"
    )

    print(
        "==================================="
    )

    print(
        "Starting web interface..."
    )

    print(
        "Listening on port 80..."
    )

    app.run(
        host="0.0.0.0",
        port=80,
        debug=False,
        threaded=True,
    )


if __name__ == "__main__":
    main()

