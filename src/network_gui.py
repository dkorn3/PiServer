```python
from flask import Flask, request, redirect, url_for, render_template_string, jsonify
from datetime import datetime
import monitoring

app = Flask(__name__)


# ============================================================
# Temporary configuration storage
# ============================================================

CONFIG = {
    "hostname": "DomPi",
    "interface": "wlan0",
    "mode": "gateway",
    "ip_address": "",
    "gateway": "",
    "netmask": "255.255.255.0",
    "dns": "",
    "dhcp_enabled": True,
    "dns_enabled": True,
    "firewall_enabled": True,
    "vpn_enabled": False,
}


LOGS = []


# ============================================================
# Configuration functions
# ============================================================

def configure_network():
    return True


def configure_dhcp():
    return True


def configure_dns():
    return True


def configure_firewall():
    return True


def configure_vpn():
    return True


def update_monitoring():
    return monitoring.get_gateway_health()


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

    return render_template_string(
        HTML,
        page="network",
        config=CONFIG,
        logs=LOGS,
        health=None
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

    {% if page == "monitoring" %}

    <script>

        async function updateMonitoring() {

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


                // CPU

                if (
                    health.system.cpu_usage !== null
                    &&
                    document.getElementById(
                        "cpu-usage"
                    )
                ) {

                    document.getElementById(
                        "cpu-usage"
                    ).textContent =
                        health.system.cpu_usage.toFixed(1)
                        + "%";

                }


                // Memory

                if (
                    health.system.memory_usage !== null
                    &&
                    document.getElementById(
                        "memory-usage"
                    )
                ) {

                    document.getElementById(
                        "memory-usage"
                    ).textContent =
                        health.system.memory_usage.toFixed(1)
                        + "%";

                }


                // Storage

                if (
                    health.system.storage_usage !== null
                    &&
                    document.getElementById(
                        "storage-usage"
                    )
                ) {

                    document.getElementById(
                        "storage-usage"
                    ).textContent =
                        health.system.storage_usage.toFixed(1)
                        + "%";

                }


                // Temperature

                if (
                    health.system.temperature !== null
                    &&
                    document.getElementById(
                        "temperature"
                    )
                ) {

                    document.getElementById(
                        "temperature"
                    ).textContent =
                        health.system.temperature.toFixed(1)
                        + " °C";

                }


                // TCP connections

                if (
                    health.connections !== null
                    &&
                    document.getElementById(
                        "connections"
                    )
                ) {

                    document.getElementById(
                        "connections"
                    ).textContent =
                        health.connections;

                }


                // VPN

                if (
                    document.getElementById(
                        "vpn-status"
                    )
                ) {

                    document.getElementById(
                        "vpn-status"
                    ).textContent =
                        health.vpn.status;

                }


                // DNS

                if (
                    document.getElementById(
                        "dns-status"
                    )
                ) {

                    document.getElementById(
                        "dns-status"
                    ).textContent =
                        health.dns
                            ? health.dns.status
                            : "unknown";

                }


                // DHCP

                if (
                    document.getElementById(
                        "dhcp-status"
                    )
                ) {

                    document.getElementById(
                        "dhcp-status"
                    ).textContent =
                        health.dhcp
                            ? health.dhcp.status
                            : "unknown";

                }


                // SSH

                if (
                    document.getElementById(
                        "ssh-status"
                    )
                ) {

                    document.getElementById(
                        "ssh-status"
                    ).textContent =
                        health.services.ssh;

                }


                // WireGuard

                if (
                    document.getElementById(
                        "wireguard-status"
                    )
                ) {

                    document.getElementById(
                        "wireguard-status"
                    ).textContent =
                        health.services.wireguard;

                }


                // Uptime

                if (
                    health.system.uptime !== null
                    &&
                    document.getElementById(
                        "uptime"
                    )
                ) {

                    document.getElementById(
                        "uptime"
                    ).textContent =
                        Math.round(
                            health.system.uptime
                        )
                        + " seconds";

                }

            }

            catch (error) {

                console.error(
                    "Monitoring update failed:",
                    error
                );

            }

        }


        // Run immediately

        updateMonitoring();


        // Update every 2 seconds

        setInterval(
            updateMonitoring,
            2000
        );

    </script>

    {% endif %}


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
```
