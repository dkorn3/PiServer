
from flask import Flask, request, redirect, url_for, render_template_string, jsonify
from datetime import datetime
import config as gateway_config
import network as network_backend
import dns as dns_backend
import dhcp as dhcp_backend
import firewall as firewall_backend
import monitoring
import gateway_logger as gateway_logging

app = Flask(__name__)


# ============================================================
# Temporary configuration storage
# ============================================================

try:
    _BOOT_CONFIG = gateway_config.load_config()
    _BOOT_NETWORK = _BOOT_CONFIG["network"]
    _BOOT_DNS = _BOOT_CONFIG["dns"]
    _BOOT_DHCP = _BOOT_CONFIG["dhcp"]
    _BOOT_FIREWALL = _BOOT_CONFIG["firewall"]
    _BOOT_VPN = _BOOT_CONFIG["vpn"]
except Exception:
    _BOOT_CONFIG = {}
    _BOOT_NETWORK = {}
    _BOOT_DNS = {}
    _BOOT_DHCP = {}
    _BOOT_FIREWALL = {}
    _BOOT_VPN = {}


CONFIG = {
    "hostname": _BOOT_CONFIG.get("hostname", "DomPi"),
    "interface": _BOOT_NETWORK.get("wan_interface", "wlan0"),
    "mode": "gateway",
    "ip_address": _BOOT_NETWORK.get("lan_address", "").split("/")[0],
    "gateway": "",
    "netmask": "255.255.255.0",
    "dns": (
        _BOOT_DNS.get("upstream_servers", ["1.1.1.1"])[0]
        if _BOOT_DNS
        else "1.1.1.1"
    ),
    "dhcp_enabled": _BOOT_DHCP.get("enabled", True),
    "dns_enabled": _BOOT_DNS.get("enabled", True),
    "firewall_enabled": _BOOT_FIREWALL.get("enabled", True),
    "vpn_enabled": _BOOT_VPN.get("enabled", False),
}


LOGS = []


# ============================================================
# Configuration functions
# ============================================================

def _current_backend_config():
    """Translate the GUI's temporary CONFIG format into gateway config."""
    cfg = gateway_config.load_config()

    cfg["hostname"] = CONFIG["hostname"]

    cfg["network"]["wan_interface"] = CONFIG["interface"]
    cfg["network"]["lan_interface"] = cfg["network"].get(
        "lan_interface",
        "eth1"
    )

    if CONFIG["ip_address"]:
        cfg["network"]["lan_address"] = (
            f'{CONFIG["ip_address"]}/{CONFIG["netmask"]}'
        )

    return cfg


def configure_network():
    cfg = _current_backend_config()

    gateway_config.save_config(cfg)
    gateway_logging.log_info("Network configuration updated.")

    return True


def configure_dhcp():
    cfg = _current_backend_config()

    dhcp_cfg = dict(cfg["dhcp"])
    dhcp_cfg["interface"] = cfg["network"]["lan_interface"]
    dhcp_cfg["address"] = cfg["network"]["lan_address"].split("/")[0]

    if CONFIG["dhcp_enabled"]:
        success = dhcp_backend.configure_dhcp(dhcp_cfg)
    else:
        import subprocess
        success = (
            subprocess.run(
                ["systemctl", "stop", "dnsmasq"],
                capture_output=True,
                text=True,
                check=False,
            ).returncode == 0
        )

    gateway_logging.log_info(
        "DHCP configuration applied."
        if success
        else "DHCP configuration failed."
    )

    return success


def configure_dns():
    cfg = _current_backend_config()

    servers = cfg["dns"]["upstream_servers"]

    if not CONFIG["dns_enabled"]:
        import subprocess
        result = subprocess.run(
            ["systemctl", "stop", "dnsmasq"],
            capture_output=True,
            text=True,
            check=False,
        )
        success = result.returncode == 0
    else:
        dns_backend.set_upstream_servers(servers)
        success = True

    gateway_logging.log_info(
        "DNS configuration updated."
        if success
        else "DNS configuration failed."
    )

    return success


def configure_firewall():
    cfg = _current_backend_config()

    lan = cfg["network"]["lan_interface"]
    wan = cfg["network"]["wan_interface"]

    if not CONFIG["firewall_enabled"]:
        import subprocess
        result = subprocess.run(
            ["systemctl", "stop", "nftables"],
            capture_output=True,
            text=True,
            check=False,
        )
        success = result.returncode == 0
    else:
        firewall_backend.save_ruleset(lan, wan)
        success = firewall_backend.apply_firewall_rules(lan, wan)

    gateway_logging.log_info(
        "Firewall configuration updated."
        if success
        else "Firewall configuration failed."
    )

    return success


def configure_vpn():
    gateway_logging.log_info(
        "VPN configuration toggle updated."
    )
    return True


def update_monitoring():
    return monitoring.get_gateway_health()


def update_network_status():
    """Return the live Linux network state for the Network page."""
    try:
        return network_backend.get_network_status()
    except Exception as exc:
        return {
            "interfaces": {},
            "default_route": None,
            "ipv4_forwarding": None,
            "routes": [],
            "error": str(exc),
        }


# ============================================================
# Logging
# ============================================================

def add_log(message):

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    LOGS.insert(
        0,
        {
            "time": timestamp,
            "message": message
        }
    )

    if len(LOGS) > 100:
        LOGS.pop()

    try:
        gateway_logging.log_info(message)
    except Exception:
        pass


# ============================================================
# Main dashboard
# ============================================================

@app.route("/")
def dashboard():

    health = update_monitoring()

    return render_template_string(
        HTML,
        page="dashboard",
        config=CONFIG,
        logs=LOGS,
        health=health
    )


# ============================================================
# Network
# ============================================================

@app.route("/network", methods=["GET", "POST"])
def network():

    if request.method == "POST":

        CONFIG["hostname"] = request.form.get(
            "hostname",
            CONFIG["hostname"]
        )

        CONFIG["interface"] = request.form.get(
            "interface",
            CONFIG["interface"]
        )

        CONFIG["mode"] = request.form.get(
            "mode",
            CONFIG["mode"]
        )

        CONFIG["ip_address"] = request.form.get(
            "ip_address",
            CONFIG["ip_address"]
        )

        CONFIG["gateway"] = request.form.get(
            "gateway",
            CONFIG["gateway"]
        )

        CONFIG["netmask"] = request.form.get(
            "netmask",
            CONFIG["netmask"]
        )

        CONFIG["dns"] = request.form.get(
            "dns",
            CONFIG["dns"]
        )

        configure_network()

        add_log(
            "Network configuration updated."
        )

        return redirect(url_for("network"))

    network_status = update_network_status()

    return render_template_string(
        HTML,
        page="network",
        config=CONFIG,
        logs=LOGS,
        health=None,
        network_status=network_status
    )


# ============================================================
# DHCP
# ============================================================

@app.route("/dhcp", methods=["GET", "POST"])
def dhcp():

    if request.method == "POST":

        CONFIG["dhcp_enabled"] = (
            request.form.get("dhcp_enabled") == "on"
        )

        configure_dhcp()

        add_log(
            "DHCP "
            + (
                "enabled."
                if CONFIG["dhcp_enabled"]
                else "disabled."
            )
        )

        return redirect(url_for("dhcp"))

    return render_template_string(
        HTML,
        page="dhcp",
        config=CONFIG,
        logs=LOGS,
        health=None
    )


# ============================================================
# DNS
# ============================================================

@app.route("/dns", methods=["GET", "POST"])
def dns():

    if request.method == "POST":

        CONFIG["dns_enabled"] = (
            request.form.get("dns_enabled") == "on"
        )

        configure_dns()

        add_log(
            "DNS "
            + (
                "enabled."
                if CONFIG["dns_enabled"]
                else "disabled."
            )
        )

        return redirect(url_for("dns"))

    return render_template_string(
        HTML,
        page="dns",
        config=CONFIG,
        logs=LOGS,
        health=None
    )


# ============================================================
# Firewall
# ============================================================

@app.route("/firewall", methods=["GET", "POST"])
def firewall():

    if request.method == "POST":

        CONFIG["firewall_enabled"] = (
            request.form.get("firewall_enabled") == "on"
        )

        configure_firewall()

        add_log(
            "Firewall "
            + (
                "enabled."
                if CONFIG["firewall_enabled"]
                else "disabled."
            )
        )

        return redirect(url_for("firewall"))

    return render_template_string(
        HTML,
        page="firewall",
        config=CONFIG,
        logs=LOGS,
        health=None
    )


# ============================================================
# VPN
# ============================================================

@app.route("/vpn", methods=["GET", "POST"])
def vpn():

    if request.method == "POST":

        CONFIG["vpn_enabled"] = (
            request.form.get("vpn_enabled") == "on"
        )

        configure_vpn()

        add_log(
            "VPN "
            + (
                "enabled."
                if CONFIG["vpn_enabled"]
                else "disabled."
            )
        )

        return redirect(url_for("vpn"))

    return render_template_string(
        HTML,
        page="vpn",
        config=CONFIG,
        logs=LOGS,
        health=None
    )


# ============================================================
# Monitoring
# ============================================================

@app.route("/monitoring")
def monitoring_page():

    health = update_monitoring()

    return render_template_string(
        HTML,
        page="monitoring",
        config=CONFIG,
        logs=LOGS,
        health=health
    )


# ============================================================
# Monitoring API
# ============================================================

@app.route("/api/monitoring")
def monitoring_api():

    health = update_monitoring()

    return jsonify(health)


# ============================================================
# Logs
# ============================================================

@app.route("/logs")
def logs():

    return render_template_string(
        HTML,
        page="logs",
        config=CONFIG,
        logs=LOGS,
        health=None
    )


# ============================================================
# HTML
# ============================================================

HTML = """

<!DOCTYPE html>

<html>

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
                Arial,
                sans-serif;

            background: #f4f6f8;

            color: #222;
        }


        .sidebar {

            position: fixed;

            left: 0;
            top: 0;
            bottom: 0;

            width: 230px;

            background: #111827;

            color: white;

            padding: 25px 15px;
        }


        .logo {

            font-size: 25px;

            font-weight: bold;

            padding: 0 15px 30px 15px;
        }


        .nav {

            display: flex;

            flex-direction: column;

            gap: 6px;
        }


        .nav a {

            color: #d1d5db;

            text-decoration: none;

            padding: 12px 15px;

            border-radius: 8px;

            font-size: 15px;
        }


        .nav a:hover {

            background: #1f2937;

            color: white;
        }


        .nav a.active {

            background: #374151;

            color: white;
        }


        .main {

            margin-left: 230px;

            padding: 35px;

            max-width: 1400px;
        }


        .header {

            display: flex;

            justify-content: space-between;

            align-items: center;

            margin-bottom: 30px;
        }


        .header h1 {

            margin: 0;

            font-size: 30px;
        }


        .status {

            display: flex;

            align-items: center;

            gap: 8px;

            font-size: 14px;

            color: #555;
        }


        .status-dot {

            width: 10px;
            height: 10px;

            border-radius: 50%;

            background: #22c55e;
        }


        .cards {

            display: grid;

            grid-template-columns:
                repeat(auto-fit, minmax(210px, 1fr));

            gap: 18px;

            margin-bottom: 25px;
        }


        .card {

            background: white;

            border-radius: 12px;

            padding: 22px;

            box-shadow:
                0 2px 8px rgba(0, 0, 0, 0.06);
        }


        .card-title {

            font-size: 14px;

            color: #6b7280;

            margin-bottom: 10px;
        }


        .card-value {

            font-size: 27px;

            font-weight: 600;
        }


        .green {
            color: #16a34a;
        }


        .yellow {
            color: #ca8a04;
        }


        .red {
            color: #dc2626;
        }


        .section {

            background: white;

            border-radius: 12px;

            padding: 25px;

            margin-bottom: 25px;

            box-shadow:
                0 2px 8px rgba(0, 0, 0, 0.06);
        }


        .section h2 {

            margin-top: 0;

            margin-bottom: 20px;

            font-size: 20px;
        }


        .form-group {
            margin-bottom: 18px;
        }


        label {

            display: block;

            font-size: 14px;

            font-weight: 500;

            margin-bottom: 7px;
        }


        input,
        select {

            width: 100%;

            padding: 11px 12px;

            border: 1px solid #d1d5db;

            border-radius: 7px;

            font-size: 14px;

            background: white;
        }


        input:focus,
        select:focus {

            outline: none;

            border-color: #6b7280;
        }


        .button {

            border: none;

            background: #111827;

            color: white;

            padding: 11px 18px;

            border-radius: 7px;

            cursor: pointer;

            font-size: 14px;
        }


        .button:hover {
            background: #374151;
        }


        .toggle-row {

            display: flex;

            justify-content: space-between;

            align-items: center;

            padding: 15px 0;

            border-bottom: 1px solid #eee;
        }


        .toggle-row:last-child {
            border-bottom: none;
        }


        .toggle-switch {

            position: relative;

            width: 48px;
            height: 26px;
        }


        .toggle-switch input {

            opacity: 0;

            width: 0;
            height: 0;
        }


        .slider {

            position: absolute;

            cursor: pointer;

            top: 0;
            left: 0;
            right: 0;
            bottom: 0;

            background: #d1d5db;

            border-radius: 30px;

            transition: 0.2s;
        }


        .slider:before {

            content: "";

            position: absolute;

            height: 20px;
            width: 20px;

            left: 3px;
            top: 3px;

            background: white;

            border-radius: 50%;

            transition: 0.2s;
        }


        .toggle-switch input:checked + .slider {
            background: #22c55e;
        }


        .toggle-switch input:checked + .slider:before {
            transform: translateX(22px);
        }


        .log-entry {

            padding: 13px 0;

            border-bottom: 1px solid #eee;

            display: flex;

            gap: 20px;
        }


        .log-time {

            color: #6b7280;

            font-size: 13px;

            min-width: 160px;
        }


        .log-message {
            font-size: 14px;
        }


        .info-grid {

            display: grid;

            grid-template-columns:
                repeat(auto-fit, minmax(250px, 1fr));

            gap: 15px;
        }


        .info-item {

            padding: 15px;

            background: #f9fafb;

            border-radius: 8px;
        }


        .info-label {

            font-size: 12px;

            color: #6b7280;

            margin-bottom: 5px;
        }


        .info-value {

            font-size: 16px;

            font-weight: 500;
        }


        @media (max-width: 700px) {

            .sidebar {

                width: 100%;

                height: auto;

                position: relative;
            }


            .nav {

                flex-direction: row;

                flex-wrap: wrap;
            }


            .main {

                margin-left: 0;

                padding: 20px;
            }

        }

    </style>

</head>


<body>


    <!-- Sidebar -->

    <div class="sidebar">

        <div class="logo">
            PiServer
        </div>


        <div class="nav">

            <a
                href="/"
                class="{% if page == 'dashboard' %}active{% endif %}"
            >
                Dashboard
            </a>


            <a
                href="/network"
                class="{% if page == 'network' %}active{% endif %}"
            >
                Network
            </a>


            <a
                href="/dhcp"
                class="{% if page == 'dhcp' %}active{% endif %}"
            >
                DHCP
            </a>


            <a
                href="/dns"
                class="{% if page == 'dns' %}active{% endif %}"
            >
                DNS
            </a>


            <a
                href="/firewall"
                class="{% if page == 'firewall' %}active{% endif %}"
            >
                Firewall
            </a>


            <a
                href="/vpn"
                class="{% if page == 'vpn' %}active{% endif %}"
            >
                VPN
            </a>


            <a
                href="/monitoring"
                class="{% if page == 'monitoring' %}active{% endif %}"
            >
                Monitoring
            </a>


            <a
                href="/logs"
                class="{% if page == 'logs' %}active{% endif %}"
            >
                Logs
            </a>

        </div>

    </div>


    <!-- Main -->

    <div class="main">


        <div class="header">

            <h1>

                {% if page == "dashboard" %}
                    Dashboard
                {% elif page == "network" %}
                    Network
                {% elif page == "dhcp" %}
                    DHCP
                {% elif page == "dns" %}
                    DNS
                {% elif page == "firewall" %}
                    Firewall
                {% elif page == "vpn" %}
                    VPN
                {% elif page == "monitoring" %}
                    Monitoring
                {% elif page == "logs" %}
                    Logs
                {% endif %}

            </h1>


            <div class="status">

                <div class="status-dot"></div>

                PiServer Online

            </div>

        </div>


        <!-- ================================================= -->
        <!-- DASHBOARD -->
        <!-- ================================================= -->

        {% if page == "dashboard" %}


            <div class="cards">


                <div class="card">

                    <div class="card-title">
                        CPU Usage
                    </div>

                    <div
                        class="card-value"
                        id="dashboard-cpu-usage"
                    >

                        {% if health.system.cpu_usage is not none %}
                            {{ "%.1f"|format(health.system.cpu_usage) }}%
                        {% else %}
                            --
                        {% endif %}

                    </div>

                </div>


                <div class="card">

                    <div class="card-title">
                        Memory
                    </div>

                    <div
                        class="card-value"
                        id="dashboard-memory-usage"
                    >

                        {% if health.system.memory_usage is not none %}
                            {{ "%.1f"|format(health.system.memory_usage) }}%
                        {% else %}
                            --
                        {% endif %}

                    </div>

                </div>


                <div class="card">

                    <div class="card-title">
                        Temperature
                    </div>

                    <div
                        class="card-value"
                        id="dashboard-temperature"
                    >

                        {% if health.system.temperature is not none %}
                            {{ "%.1f"|format(health.system.temperature) }} °C
                        {% else %}
                            --
                        {% endif %}

                    </div>

                </div>


                <div class="card">

                    <div class="card-title">
                        TCP Connections
                    </div>

                    <div
                        class="card-value"
                        id="dashboard-connections"
                    >

                        {% if health.connections is not none %}
                            {{ health.connections }}
                        {% else %}
                            --
                        {% endif %}

                    </div>

                </div>


            </div>


            <div class="section">

                <h2>
                    Gateway Services
                </h2>


                <div class="info-grid">


                    <div class="info-item">

                        <div class="info-label">
                            SSH
                        </div>

                        <div
                            class="info-value"
                            id="dashboard-ssh-status"
                        >

                            {% if health.services.ssh == "active" %}

                                <span class="green">
                                    Active
                                </span>

                            {% else %}

                                <span class="red">
                                    {{ health.services.ssh }}
                                </span>

                            {% endif %}

                        </div>

                    </div>


                    <div class="info-item">

                        <div class="info-label">
                            WireGuard
                        </div>

                        <div
                            class="info-value"
                            id="dashboard-wireguard-status"
                        >

                            {% if health.services.wireguard == "active" %}

                                <span class="green">
                                    Active
                                </span>

                            {% else %}

                                <span class="yellow">
                                    {{ health.services.wireguard }}
                                </span>

                            {% endif %}

                        </div>

                    </div>


                </div>

            </div>


        <!-- ================================================= -->
        <!-- NETWORK -->
        <!-- ================================================= -->

        {% elif page == "network" %}


            <div class="section">

                <h2>
                    Network Configuration
                </h2>


                <form method="POST">


                    <div class="form-group">

                        <label>
                            Hostname
                        </label>

                        <input
                            type="text"
                            name="hostname"
                            value="{{ config.hostname }}"
                        >

                    </div>


                    <div class="form-group">

                        <label>
                            Interface
                        </label>

                        <input
                            type="text"
                            name="interface"
                            value="{{ config.interface }}"
                        >

                    </div>


                    <div class="form-group">

                        <label>
                            Mode
                        </label>

                        <select name="mode">

                            <option
                                value="gateway"
                                {% if config.mode == "gateway" %}
                                selected
                                {% endif %}
                            >
                                Gateway
                            </option>

                            <option
                                value="router"
                                {% if config.mode == "router" %}
                                selected
                                {% endif %}
                            >
                                Router
                            </option>

                            <option
                                value="access_point"
                                {% if config.mode == "access_point" %}
                                selected
                                {% endif %}
                            >
                                Access Point
                            </option>

                        </select>

                    </div>


                    <div class="form-group">

                        <label>
                            IP Address
                        </label>

                        <input
                            type="text"
                            name="ip_address"
                            value="{{ config.ip_address }}"
                            placeholder="192.168.1.1"
                        >

                    </div>


                    <div class="form-group">

                        <label>
                            Gateway
                        </label>

                        <input
                            type="text"
                            name="gateway"
                            value="{{ config.gateway }}"
                            placeholder="192.168.1.1"
                        >

                    </div>


                    <div class="form-group">

                        <label>
                            Netmask
                        </label>

                        <input
                            type="text"
                            name="netmask"
                            value="{{ config.netmask }}"
                        >

                    </div>


                    <div class="form-group">

                        <label>
                            DNS Server
                        </label>

                        <input
                            type="text"
                            name="dns"
                            value="{{ config.dns }}"
                            placeholder="1.1.1.1"
                        >

                    </div>


                    <button
                        type="submit"
                        class="button"
                    >
                        Save Network Configuration
                    </button>


                </form>

            </div>
            <div class="section">

                <h2>
                    Live Network Status
                </h2>

                {% if network_status.error %}

                    <div class="info-item">
                        <div class="info-label">
                            Error
                        </div>

                        <div class="info-value red">
                            {{ network_status.error }}
                        </div>
                    </div>

                {% else %}

                    <div class="cards">

                        <div class="card">

                            <div class="card-title">
                                Default Route
                            </div>

                            <div class="card-value">
                                {{ network_status.default_route or "--" }}
                            </div>

                        </div>


                        <div class="card">

                            <div class="card-title">
                                IPv4 Forwarding
                            </div>

                            <div class="card-value">

                                {% if network_status.ipv4_forwarding %}
                                    <span class="green">
                                        Enabled
                                    </span>
                                {% elif network_status.ipv4_forwarding is false %}
                                    <span class="yellow">
                                        Disabled
                                    </span>
                                {% else %}
                                    <span class="red">
                                        Unknown
                                    </span>
                                {% endif %}

                            </div>

                        </div>


                        <div class="card">

                            <div class="card-title">
                                Interfaces
                            </div>

                            <div class="card-value">
                                {{ network_status.interfaces|length }}
                            </div>

                        </div>

                    </div>


                    <div class="section">

                        <h2>
                            Interfaces
                        </h2>

                        <div style="overflow-x: auto;">

                            <table style="
                                width: 100%;
                                border-collapse: collapse;
                                font-size: 14px;
                            ">

                                <thead>

                                    <tr>
                                        <th style="text-align: left; padding: 10px;">
                                            Name
                                        </th>

                                        <th style="text-align: left; padding: 10px;">
                                            Type
                                        </th>

                                        <th style="text-align: left; padding: 10px;">
                                            Status
                                        </th>

                                        <th style="text-align: left; padding: 10px;">
                                            MAC
                                        </th>

                                        <th style="text-align: left; padding: 10px;">
                                            Addresses
                                        </th>
                                    </tr>

                                </thead>

                                <tbody>

                                    {% for name, interface in network_status.interfaces.items() %}

                                        <tr>

                                            <td style="padding: 10px;">
                                                {{ name }}
                                            </td>

                                            <td style="padding: 10px;">
                                                {{ interface.type or "--" }}
                                            </td>

                                            <td style="padding: 10px;">

                                                {% if interface.status == "up" %}

                                                    <span class="green">
                                                        UP
                                                    </span>

                                                {% elif interface.status == "down" %}

                                                    <span class="red">
                                                        DOWN
                                                    </span>

                                                {% else %}

                                                    <span class="yellow">
                                                        {{ interface.status or "UNKNOWN" }}
                                                    </span>

                                                {% endif %}

                                            </td>

                                            <td style="padding: 10px;">
                                                {{ interface.mac or "--" }}
                                            </td>

                                            <td style="padding: 10px;">

                                                {% if interface.addresses %}

                                                    {{ interface.addresses|join(", ") }}

                                                {% else %}

                                                    --

                                                {% endif %}

                                            </td>

                                        </tr>

                                    {% endfor %}

                                </tbody>

                            </table>

                        </div>

                    </div>


                    <div class="section">

                        <h2>
                            Routing Table
                        </h2>

                        {% if network_status.routes %}

                            {% for route in network_status.routes %}

                                <div class="info-item" style="margin-bottom: 8px;">
                                    {{ route }}
                                </div>

                            {% endfor %}

                        {% else %}

                            <div class="info-label">
                                No routes found.
                            </div>

                        {% endif %}

                    </div>

                {% endif %}

            </div>

        <!-- ================================================= -->
        <!-- DHCP -->
        <!-- ================================================= -->

        {% elif page == "dhcp" %}


            <div class="section">

                <h2>
                    DHCP Server
                </h2>


                <form method="POST">


                    <div class="toggle-row">

                        <div>

                            <strong>
                                DHCP Server
                            </strong>

                            <div class="info-label">
                                Automatically assign IP addresses
                            </div>

                        </div>


                        <label class="toggle-switch">

                            <input
                                type="checkbox"
                                name="dhcp_enabled"
                                {% if config.dhcp_enabled %}
                                checked
                                {% endif %}
                            >

                            <span class="slider"></span>

                        </label>

                    </div>


                    <br>


                    <button
                        type="submit"
                        class="button"
                    >
                        Save DHCP Configuration
                    </button>


                </form>

            </div>


        <!-- ================================================= -->
        <!-- DNS -->
        <!-- ================================================= -->

        {% elif page == "dns" %}


            <div class="section">

                <h2>
                    DNS
                </h2>


                <form method="POST">


                    <div class="toggle-row">

                        <div>

                            <strong>
                                DNS Service
                            </strong>

                            <div class="info-label">
                                Enable PiServer DNS functionality
                            </div>

                        </div>


                        <label class="toggle-switch">

                            <input
                                type="checkbox"
                                name="dns_enabled"
                                {% if config.dns_enabled %}
                                checked
                                {% endif %}
                            >

                            <span class="slider"></span>

                        </label>

                    </div>


                    <br>


                    <button
                        type="submit"
                        class="button"
                    >
                        Save DNS Configuration
                    </button>


                </form>

            </div>


        <!-- ================================================= -->
        <!-- FIREWALL -->
        <!-- ================================================= -->

        {% elif page == "firewall" %}


            <div class="section">

                <h2>
                    Firewall
                </h2>


                <form method="POST">


                    <div class="toggle-row">

                        <div>

                            <strong>
                                Firewall
                            </strong>

                            <div class="info-label">
                                Enable gateway firewall protection
                            </div>

                        </div>


                        <label class="toggle-switch">

                            <input
                                type="checkbox"
                                name="firewall_enabled"
                                {% if config.firewall_enabled %}
                                checked
                                {% endif %}
                            >

                            <span class="slider"></span>

                        </label>

                    </div>


                    <br>


                    <button
                        type="submit"
                        class="button"
                    >
                        Save Firewall Configuration
                    </button>


                </form>

            </div>


        <!-- ================================================= -->
        <!-- VPN -->
        <!-- ================================================= -->

        {% elif page == "vpn" %}


            <div class="section">

                <h2>
                    VPN
                </h2>


                <form method="POST">


                    <div class="toggle-row">

                        <div>

                            <strong>
                                WireGuard VPN
                            </strong>

                            <div class="info-label">
                                Enable WireGuard VPN gateway
                            </div>

                        </div>


                        <label class="toggle-switch">

                            <input
                                type="checkbox"
                                name="vpn_enabled"
                                {% if config.vpn_enabled %}
                                checked
                                {% endif %}
                            >

                            <span class="slider"></span>

                        </label>

                    </div>


                    <br>


                    <button
                        type="submit"
                        class="button"
                    >
                        Save VPN Configuration
                    </button>


                </form>

            </div>


        <!-- ================================================= -->
        <!-- MONITORING -->
        <!-- ================================================= -->

        {% elif page == "monitoring" %}


            <div class="cards">


                <div class="card">

                    <div class="card-title">
                        CPU Usage
                    </div>

                    <div
                        class="card-value"
                        id="cpu-usage"
                    >

                        {% if health.system.cpu_usage is not none %}
                            {{ "%.1f"|format(health.system.cpu_usage) }}%
                        {% else %}
                            --
                        {% endif %}

                    </div>

                </div>


                <div class="card">

                    <div class="card-title">
                        Memory
                    </div>

                    <div
                        class="card-value"
                        id="memory-usage"
                    >

                        {% if health.system.memory_usage is not none %}
                            {{ "%.1f"|format(health.system.memory_usage) }}%
                        {% else %}
                            --
                        {% endif %}

                    </div>

                </div>


                <div class="card">

                    <div class="card-title">
                        Storage
                    </div>

                    <div
                        class="card-value"
                        id="storage-usage"
                    >

                        {% if health.system.storage_usage is not none %}
                            {{ "%.1f"|format(health.system.storage_usage) }}%
                        {% else %}
                            --
                        {% endif %}

                    </div>

                </div>


                <div class="card">

                    <div class="card-title">
                        Temperature
                    </div>

                    <div
                        class="card-value"
                        id="temperature"
                    >

                        {% if health.system.temperature is not none %}
                            {{ "%.1f"|format(health.system.temperature) }} °C
                        {% else %}
                            --
                        {% endif %}

                    </div>

                </div>


            </div>


            <div class="cards">


                <div class="card">

                    <div class="card-title">
                        TCP Connections
                    </div>

                    <div
                        class="card-value"
                        id="connections"
                    >

                        {% if health.connections is not none %}
                            {{ health.connections }}
                        {% else %}
                            --
                        {% endif %}

                    </div>

                </div>


                <div class="card">

                    <div class="card-title">
                        VPN
                    </div>

                    <div
                        class="card-value"
                        id="vpn-status"
                    >

                        {{ health.vpn.status }}

                    </div>

                </div>


                <div class="card">

                    <div class="card-title">
                        DNS
                    </div>

                    <div
                        class="card-value"
                        id="dns-status"
                    >

                        {% if health.dns %}
                            {{ health.dns.status }}
                        {% else %}
                            unknown
                        {% endif %}

                    </div>

                </div>


                <div class="card">

                    <div class="card-title">
                        DHCP
                    </div>

                    <div
                        class="card-value"
                        id="dhcp-status"
                    >

                        {% if health.dhcp %}
                            {{ health.dhcp.status }}
                        {% else %}
                            unknown
                        {% endif %}

                    </div>

                </div>


            </div>


            <div class="section">

                <h2>
                    Gateway Services
                </h2>


                <div class="info-grid">


                    <div class="info-item">

                        <div class="info-label">
                            SSH
                        </div>

                        <div
                            class="info-value"
                            id="ssh-status"
                        >

                            {{ health.services.ssh }}

                        </div>

                    </div>


                    <div class="info-item">

                        <div class="info-label">
                            WireGuard
                        </div>

                        <div
                            class="info-value"
                            id="wireguard-status"
                        >

                            {{ health.services.wireguard }}

                        </div>

                    </div>


                    <div class="info-item">

                        <div class="info-label">
                            System Uptime
                        </div>

                        <div
                            class="info-value"
                            id="uptime"
                        >

                            {% if health.system.uptime is not none %}

                                {{ "%.0f"|format(
                                    health.system.uptime
                                ) }} seconds

                            {% else %}

                                --

                            {% endif %}

                        </div>

                    </div>


                </div>

            </div>


        <!-- ================================================= -->
        <!-- LOGS -->
        <!-- ================================================= -->

        {% elif page == "logs" %}


            <div class="section">

                <h2>
                    System Logs
                </h2>


                {% if logs %}

                    {% for log in logs %}

                        <div class="log-entry">

                            <div class="log-time">
                                {{ log.time }}
                            </div>

                            <div class="log-message">
                                {{ log.message }}
                            </div>

                        </div>

                    {% endfor %}

                {% else %}

                    <div class="info-label">
                        No logs yet.
                    </div>

                {% endif %}


            </div>


        {% endif %}


    </div>


    <!-- ===================================================== -->
    <!-- LIVE MONITORING JAVASCRIPT -->
    <!-- ===================================================== -->

    <script>

        async function updatePage() {

            try {

                const response = await fetch(
                    "/api/monitoring",
                    {
                        cache: "no-store"
                    }
                );


                if (!response.ok) {

                    throw new Error(
                        "HTTP " + response.status
                    );

                }


                const health =
                    await response.json();


                // =================================================
                // DASHBOARD
                // =================================================

                const dashboardCPU =
                    document.getElementById(
                        "dashboard-cpu-usage"
                    );

                if (
                    dashboardCPU &&
                    health.system.cpu_usage !== null
                ) {

                    dashboardCPU.textContent =
                        health.system.cpu_usage.toFixed(1)
                        + "%";

                }


                const dashboardMemory =
                    document.getElementById(
                        "dashboard-memory-usage"
                    );

                if (
                    dashboardMemory &&
                    health.system.memory_usage !== null
                ) {

                    dashboardMemory.textContent =
                        health.system.memory_usage.toFixed(1)
                        + "%";

                }


                const dashboardTemperature =
                    document.getElementById(
                        "dashboard-temperature"
                    );

                if (
                    dashboardTemperature &&
                    health.system.temperature !== null
                ) {

                    dashboardTemperature.textContent =
                        health.system.temperature.toFixed(1)
                        + " °C";

                }


                const dashboardConnections =
                    document.getElementById(
                        "dashboard-connections"
                    );

                if (
                    dashboardConnections &&
                    health.connections !== null
                ) {

                    dashboardConnections.textContent =
                        health.connections;

                }


                const dashboardSSH =
                    document.getElementById(
                        "dashboard-ssh-status"
                    );

                if (dashboardSSH) {

                    if (
                        health.services.ssh === "active"
                    ) {

                        dashboardSSH.innerHTML =
                            '<span class="green">Active</span>';

                    } else {

                        dashboardSSH.innerHTML =
                            '<span class="red">'
                            + health.services.ssh
                            + '</span>';

                    }

                }


                const dashboardWireGuard =
                    document.getElementById(
                        "dashboard-wireguard-status"
                    );

                if (dashboardWireGuard) {

                    if (
                        health.services.wireguard === "active"
                    ) {

                        dashboardWireGuard.innerHTML =
                            '<span class="green">Active</span>';

                    } else {

                        dashboardWireGuard.innerHTML =
                            '<span class="yellow">'
                            + health.services.wireguard
                            + '</span>';

                    }

                }


                // =================================================
                // MONITORING PAGE
                // =================================================

                const cpu =
                    document.getElementById(
                        "cpu-usage"
                    );

                if (
                    cpu &&
                    health.system.cpu_usage !== null
                ) {

                    cpu.textContent =
                        health.system.cpu_usage.toFixed(1)
                        + "%";

                }


                const memory =
                    document.getElementById(
                        "memory-usage"
                    );

                if (
                    memory &&
                    health.system.memory_usage !== null
                ) {

                    memory.textContent =
                        health.system.memory_usage.toFixed(1)
                        + "%";

                }


                const storage =
                    document.getElementById(
                        "storage-usage"
                    );

                if (
                    storage &&
                    health.system.storage_usage !== null
                ) {

                    storage.textContent =
                        health.system.storage_usage.toFixed(1)
                        + "%";

                }


                const temperature =
                    document.getElementById(
                        "temperature"
                    );

                if (
                    temperature &&
                    health.system.temperature !== null
                ) {

                    temperature.textContent =
                        health.system.temperature.toFixed(1)
                        + " °C";

                }


                const connections =
                    document.getElementById(
                        "connections"
                    );

                if (
                    connections &&
                    health.connections !== null
                ) {

                    connections.textContent =
                        health.connections;

                }


                const vpn =
                    document.getElementById(
                        "vpn-status"
                    );

                if (vpn) {

                    vpn.textContent =
                        health.vpn.status;

                }


                const dns =
                    document.getElementById(
                        "dns-status"
                    );

                if (dns) {

                    dns.textContent =
                        health.dns
                        ? health.dns.status
                        : "unknown";

                }


                const dhcp =
                    document.getElementById(
                        "dhcp-status"
                    );

                if (dhcp) {

                    dhcp.textContent =
                        health.dhcp
                        ? health.dhcp.status
                        : "unknown";

                }


                const ssh =
                    document.getElementById(
                        "ssh-status"
                    );

                if (ssh) {

                    ssh.textContent =
                        health.services.ssh;

                }


                const wireguard =
                    document.getElementById(
                        "wireguard-status"
                    );

                if (wireguard) {

                    wireguard.textContent =
                        health.services.wireguard;

                }


                const uptime =
                    document.getElementById(
                        "uptime"
                    );

                if (
                    uptime &&
                    health.system.uptime !== null
                ) {

                    uptime.textContent =
                        Math.round(
                            health.system.uptime
                        )
                        + " seconds";

                }

            }

            catch (error) {

                console.error(
                    "PiServer monitoring update failed:",
                    error
                );

            }

        }


        // =================================================
        // Initial update
        // =================================================

        updatePage();


        // =================================================
        // Update every 1 second
        // =================================================

        setInterval(
            updatePage,
            1000
        );

    </script>


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

    print("")


    app.run(
        host="0.0.0.0",
        port=80,
        debug=False,
        threaded=True
    )


if __name__ == "__main__":
    main()

