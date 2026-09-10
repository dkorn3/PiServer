#!/usr/bin/env python3

from flask import Flask, request, redirect, url_for, render_template_string
from datetime import datetime

app = Flask(__name__)

# ============================================================
# Temporary configuration
# Replace these with your real networking functions later.
# ============================================================

CONFIG = {
    "hostname": "raspberrypi",
    "interface": "wlan0",
    "mode": "DHCP",
    "ip_address": "192.168.1.196",
    "gateway": "192.168.1.1",
    "netmask": "255.255.255.0",
    "dns_primary": "1.1.1.1",
    "dns_secondary": "8.8.8.8",

    "dhcp_enabled": True,
    "dns_enabled": True,
    "dns_filtering": True,
    "firewall_enabled": True,
    "vpn_enabled": False,
    "vpn_kill_switch": False,
}

LOGS = [
    "Gateway GUI started",
    "Configuration loaded",
]


# ============================================================
# Placeholder functions
# Connect your real modules here later.
# ============================================================

def configure_network():
    """
    Later:
        network.configure(...)
    """
    pass


def configure_dhcp():
    """
    Later:
        dhcp.configure(...)
    """
    pass


def configure_dns():
    """
    Later:
        dns.configure(...)
    """
    pass


def configure_firewall():
    """
    Later:
        firewall.configure(...)
    """
    pass


def configure_vpn():
    """
    Later:
        vpn.configure(...)
    """
    pass


def update_monitoring():
    """
    Later:
        monitoring.update(...)
    """
    pass


def main():
    """
    Main application entry point.
    """

    print("================================")
    print(" Raspberry Pi Network Gateway")
    print("================================")
    print("Starting GUI...")
    print("Listening on port 80")

    # Future initialization:
    # configure_network()
    # configure_dhcp()
    # configure_dns()
    # configure_firewall()
    # configure_vpn()

    app.run(
        host="0.0.0.0",
        port=80,
        debug=False
    )


# ============================================================
# Routes
# ============================================================

@app.route("/")
def dashboard():
    return render_template_string(
        HTML,
        page="dashboard",
        config=CONFIG,
        logs=LOGS
    )


@app.route("/network")
def network():
    return render_template_string(
        HTML,
        page="network",
        config=CONFIG,
        logs=LOGS
    )


@app.route("/dhcp")
def dhcp():
    return render_template_string(
        HTML,
        page="dhcp",
        config=CONFIG,
        logs=LOGS
    )


@app.route("/dns")
def dns():
    return render_template_string(
        HTML,
        page="dns",
        config=CONFIG,
        logs=LOGS
    )


@app.route("/firewall")
def firewall():
    return render_template_string(
        HTML,
        page="firewall",
        config=CONFIG,
        logs=LOGS
    )


@app.route("/vpn")
def vpn():
    return render_template_string(
        HTML,
        page="vpn",
        config=CONFIG,
        logs=LOGS
    )


@app.route("/monitoring")
def monitoring():
    update_monitoring()

    return render_template_string(
        HTML,
        page="monitoring",
        config=CONFIG,
        logs=LOGS
    )


@app.route("/logs")
def logs():
    return render_template_string(
        HTML,
        page="logs",
        config=CONFIG,
        logs=LOGS
    )


# ============================================================
# Save settings
# ============================================================

@app.route("/save/network", methods=["POST"])
def save_network():

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

    CONFIG["dns_primary"] = request.form.get(
        "dns_primary",
        CONFIG["dns_primary"]
    )

    CONFIG["dns_secondary"] = request.form.get(
        "dns_secondary",
        CONFIG["dns_secondary"]
    )

    configure_network()

    LOGS.append(
        f"[{datetime.now().strftime('%H:%M:%S')}] Network settings updated"
    )

    return redirect("/network")


@app.route("/save/dhcp", methods=["POST"])
def save_dhcp():

    CONFIG["dhcp_enabled"] = "dhcp_enabled" in request.form

    configure_dhcp()

    LOGS.append(
        f"[{datetime.now().strftime('%H:%M:%S')}] DHCP settings updated"
    )

    return redirect("/dhcp")


@app.route("/save/dns", methods=["POST"])
def save_dns():

    CONFIG["dns_enabled"] = "dns_enabled" in request.form
    CONFIG["dns_filtering"] = "dns_filtering" in request.form

    configure_dns()

    LOGS.append(
        f"[{datetime.now().strftime('%H:%M:%S')}] DNS settings updated"
    )

    return redirect("/dns")


@app.route("/save/firewall", methods=["POST"])
def save_firewall():

    CONFIG["firewall_enabled"] = (
        "firewall_enabled" in request.form
    )

    configure_firewall()

    LOGS.append(
        f"[{datetime.now().strftime('%H:%M:%S')}] Firewall settings updated"
    )

    return redirect("/firewall")


@app.route("/save/vpn", methods=["POST"])
def save_vpn():

    CONFIG["vpn_enabled"] = "vpn_enabled" in request.form
    CONFIG["vpn_kill_switch"] = "vpn_kill_switch" in request.form

    configure_vpn()

    LOGS.append(
        f"[{datetime.now().strftime('%H:%M:%S')}] VPN settings updated"
    )

    return redirect("/vpn")


# ============================================================
# HTML / CSS
# ============================================================

HTML = r"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Pi Gateway</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: #0b1016;
    color: #e8edf3;
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
}

/* ==============================
   Layout
   ============================== */

.container {
    display: flex;
    min-height: 100vh;
}

/* ==============================
   Sidebar
   ============================== */

.sidebar {
    width: 240px;
    background: #111820;
    border-right: 1px solid #26313d;
    padding: 25px 15px;

    position: fixed;

    top: 0;
    bottom: 0;
    left: 0;
}

.logo {
    font-size: 21px;
    font-weight: 700;

    padding: 5px 12px 28px;
}

.logo-icon {
    color: #56d48c;
}

.nav a {

    display: block;

    text-decoration: none;

    color: #9ca9b7;

    padding: 12px;

    margin-bottom: 4px;

    border-radius: 8px;

    font-size: 14px;

    transition: 0.15s;
}

.nav a:hover {
    background: #1b2530;
    color: white;
}

.nav a.active {
    background: #1d2b37;
    color: white;
}

.sidebar-status {

    position: absolute;

    left: 15px;
    right: 15px;
    bottom: 20px;

    background: #151f29;

    border: 1px solid #26313d;

    border-radius: 8px;

    padding: 12px;

    font-size: 12px;

    color: #9ca9b7;
}

.status-dot {

    display: inline-block;

    width: 8px;
    height: 8px;

    background: #56d48c;

    border-radius: 50%;

    margin-right: 7px;
}

/* ==============================
   Main
   ============================== */

.main {

    margin-left: 240px;

    width: calc(100% - 240px);
}

.header {

    height: 70px;

    border-bottom: 1px solid #26313d;

    display: flex;

    align-items: center;

    justify-content: space-between;

    padding: 0 32px;
}

.header-title {

    font-size: 20px;

    font-weight: 600;
}

.header-status {

    font-size: 13px;

    color: #9ca9b7;
}

.online {
    color: #56d48c;
}

.content {

    padding: 30px;

    max-width: 1250px;
}

/* ==============================
   Cards
   ============================== */

.cards {

    display: grid;

    grid-template-columns:
        repeat(4, 1fr);

    gap: 15px;

    margin-bottom: 25px;
}

.card {

    background: #121a23;

    border: 1px solid #26313d;

    border-radius: 10px;

    padding: 20px;
}

.card-title {

    color: #8996a4;

    font-size: 12px;

    text-transform: uppercase;

    letter-spacing: 0.05em;
}

.card-value {

    font-size: 24px;

    font-weight: 700;

    margin-top: 8px;
}

.green {
    color: #56d48c;
}

.yellow {
    color: #e9c35b;
}

.red {
    color: #ed6d6d;
}

/* ==============================
   Sections
   ============================== */

.section-title {

    font-size: 16px;

    font-weight: 600;

    margin-bottom: 15px;
}

.setting-row {

    display: flex;

    align-items: center;

    justify-content: space-between;

    padding: 15px 0;

    border-bottom: 1px solid #26313d;
}

.setting-row:last-child {
    border-bottom: none;
}

/* ==============================
   Forms
   ============================== */

.form-grid {

    display: grid;

    grid-template-columns:
        repeat(2, 1fr);

    gap: 18px;

    margin-top: 15px;
}

.form-group {

    display: flex;

    flex-direction: column;

    gap: 7px;
}

.form-group label {

    color: #aab5c2;

    font-size: 13px;
}

input,
select {

    width: 100%;

    padding: 11px;

    background: #0c1218;

    color: white;

    border: 1px solid #303c48;

    border-radius: 7px;

    outline: none;

    font-size: 14px;
}

input:focus,
select:focus {

    border-color: #56d48c;
}

/* ==============================
   Buttons
   ============================== */

.button {

    margin-top: 22px;

    padding: 11px 18px;

    border-radius: 7px;

    border: none;

    background: #56d48c;

    color: #08100c;

    font-weight: 700;

    cursor: pointer;
}

.button:hover {
    opacity: 0.9;
}

/* ==============================
   Toggle
   ============================== */

.toggle {

    width: 45px;
    height: 25px;

    border-radius: 20px;

    background: #394550;

    position: relative;
}

.toggle.on {
    background: #33865b;
}

.toggle::after {

    content: "";

    position: absolute;

    width: 19px;
    height: 19px;

    top: 3px;
    left: 3px;

    background: white;

    border-radius: 50%;
}

.toggle.on::after {
    left: 23px;
}

/* ==============================
   Tables
   ============================== */

table {

    width: 100%;

    border-collapse: collapse;
}

th,
td {

    padding: 13px;

    border-bottom: 1px solid #26313d;

    text-align: left;

    font-size: 13px;
}

th {
    color: #8996a4;
}

/* ==============================
   Logs
   ============================== */

.logs {

    background: #080c10;

    border: 1px solid #26313d;

    border-radius: 8px;

    padding: 18px;

    font-family: monospace;

    font-size: 12px;

    line-height: 1.9;

    color: #aab5c2;
}

/* ==============================
   Mobile
   ============================== */

@media(max-width: 850px) {

    .sidebar {
        width: 70px;
    }

    .logo {
        font-size: 0;
    }

    .logo-icon {
        font-size: 20px;
    }

    .nav a {
        font-size: 0;
        text-align: center;
    }

    .nav a:first-letter {
        font-size: 18px;
    }

    .sidebar-status {
        display: none;
    }

    .main {
        margin-left: 70px;
        width: calc(100% - 70px);
    }

    .cards {
        grid-template-columns: repeat(2, 1fr);
    }

    .form-grid {
        grid-template-columns: 1fr;
    }
}

</style>

</head>


<body>


<div class="container">


<!-- =========================================
     SIDEBAR
     ========================================= -->

<aside class="sidebar">

    <div class="logo">

        <span class="logo-icon">🛡</span>

        Pi Gateway

    </div>


    <nav class="nav">

        <a href="/"
           class="{% if page == 'dashboard' %}active{% endif %}">
            ◈ Dashboard
        </a>

        <a href="/network"
           class="{% if page == 'network' %}active{% endif %}">
            ↔ Network
        </a>

        <a href="/dhcp"
           class="{% if page == 'dhcp' %}active{% endif %}">
            ▣ DHCP
        </a>

        <a href="/dns"
           class="{% if page == 'dns' %}active{% endif %}">
            ⌁ DNS
        </a>

        <a href="/firewall"
           class="{% if page == 'firewall' %}active{% endif %}">
            ◉ Firewall
        </a>

        <a href="/vpn"
           class="{% if page == 'vpn' %}active{% endif %}">
            ⇄ VPN
        </a>

        <a href="/monitoring"
           class="{% if page == 'monitoring' %}active{% endif %}">
            ◌ Monitoring
        </a>

        <a href="/logs"
           class="{% if page == 'logs' %}active{% endif %}">
            ≡ Logs
        </a>

    </nav>


    <div class="sidebar-status">

        <span class="status-dot"></span>

        Gateway online

    </div>

</aside>


<!-- =========================================
     MAIN
     ========================================= -->

<main class="main">


<header class="header">

    <div class="header-title">

        {% if page == "dashboard" %}
            Dashboard

        {% elif page == "network" %}
            Network Settings

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

    </div>


    <div class="header-status">

        Raspberry Pi
        &nbsp;•&nbsp;

        <span class="online">
            ● Online
        </span>

    </div>

</header>


<div class="content">


<!-- =========================================
     DASHBOARD
     ========================================= -->

{% if page == "dashboard" %}


<div class="cards">


    <div class="card">

        <div class="card-title">
            Internet
        </div>

        <div class="card-value green">
            Online
        </div>

    </div>


    <div class="card">

        <div class="card-title">
            Interface
        </div>

        <div class="card-value">
            {{ config.interface }}
        </div>

    </div>


    <div class="card">

        <div class="card-title">
            IP Address
        </div>

        <div class="card-value">
            {{ config.ip_address }}
        </div>

    </div>


    <div class="card">

        <div class="card-title">
            VPN
        </div>

        <div class="card-value
            {% if config.vpn_enabled %}
                green
            {% else %}
                yellow
            {% endif %}">

            {% if config.vpn_enabled %}
                Connected
            {% else %}
                Off
            {% endif %}

        </div>

    </div>

</div>


<div class="card">

    <div class="section-title">
        Services
    </div>


    <div class="setting-row">

        <span>DHCP Server</span>

        <span class="green">
            ● Running
        </span>

    </div>


    <div class="setting-row">

        <span>DNS Service</span>

        <span class="green">
            ● Running
        </span>

    </div>


    <div class="setting-row">

        <span>Firewall</span>

        <span class="green">
            ● Active
        </span>

    </div>


    <div class="setting-row">

        <span>VPN</span>

        {% if config.vpn_enabled %}

            <span class="green">
                ● Active
            </span>

        {% else %}

            <span>
                Disabled
            </span>

        {% endif %}

    </div>

</div>


<!-- =========================================
     NETWORK
     ========================================= -->

{% elif page == "network" %}


<div class="card">

    <div class="section-title">
        Network Configuration
    </div>


    <form method="POST"
          action="/save/network">


        <div class="form-grid">


            <div class="form-group">

                <label>
                    Hostname
                </label>

                <input
                    name="hostname"
                    value="{{ config.hostname }}"
                >

            </div>


            <div class="form-group">

                <label>
                    Interface
                </label>

                <select name="interface">

                    <option
                    {% if config.interface == "wlan0" %}
                        selected
                    {% endif %}>
                        wlan0
                    </option>

                    <option
                    {% if config.interface == "eth0" %}
                        selected
                    {% endif %}>
                        eth0
                    </option>

                </select>

            </div>


            <div class="form-group">

                <label>
                    Address Mode
                </label>

                <select name="mode">

                    <option
                    {% if config.mode == "DHCP" %}
                        selected
                    {% endif %}>
                        DHCP
                    </option>

                    <option
                    {% if config.mode == "Static" %}
                        selected
                    {% endif %}>
                        Static
                    </option>

                </select>

            </div>


            <div class="form-group">

                <label>
                    IP Address
                </label>

                <input
                    name="ip_address"
                    value="{{ config.ip_address }}"
                >

            </div>


            <div class="form-group">

                <label>
                    Gateway
                </label>

                <input
                    name="gateway"
                    value="{{ config.gateway }}"
                >

            </div>


            <div class="form-group">

                <label>
                    Netmask
                </label>

                <input
                    name="netmask"
                    value="{{ config.netmask }}"
                >

            </div>


            <div class="form-group">

                <label>
                    Primary DNS
                </label>

                <input
                    name="dns_primary"
                    value="{{ config.dns_primary }}"
                >

            </div>


            <div class="form-group">

                <label>
                    Secondary DNS
                </label>

                <input
                    name="dns_secondary"
                    value="{{ config.dns_secondary }}"
                >

            </div>


        </div>


        <button class="button">
            Save Network Settings
        </button>


    </form>

</div>


<!-- =========================================
     DHCP
     ========================================= -->

{% elif page == "dhcp" %}


<div class="card">

    <div class="section-title">
        DHCP Server
    </div>


    <form method="POST"
          action="/save/dhcp">


        <div class="setting-row">

            <span>
                DHCP Server
            </span>

            <div class="toggle
                {% if config.dhcp_enabled %}
                    on
                {% endif %}">
            </div>

        </div>


        <div class="form-grid">


            <div class="form-group">

                <label>
                    Pool Start
                </label>

                <input value="192.168.1.100">

            </div>


            <div class="form-group">

                <label>
                    Pool End
                </label>

                <input value="192.168.1.200">

            </div>


            <div class="form-group">

                <label>
                    Lease Time
                </label>

                <input value="24h">

            </div>


            <div class="form-group">

                <label>
                    Default Gateway
                </label>

                <input value="{{ config.gateway }}">

            </div>


        </div>


        <button class="button">
            Save DHCP Settings
        </button>

    </form>

</div>


<!-- =========================================
     DNS
     ========================================= -->

{% elif page == "dns" %}


<div class="card">

    <div class="section-title">
        DNS Configuration
    </div>


    <form method="POST"
          action="/save/dns">


        <div class="setting-row">

            <span>
                DNS Service
            </span>

            <div class="toggle
                {% if config.dns_enabled %}
                    on
                {% endif %}">
            </div>

        </div>


        <div class="setting-row">

            <span>
                DNS Filtering
            </span>

            <div class="toggle
                {% if config.dns_filtering %}
                    on
                {% endif %}">
            </div>

        </div>


        <div class="form-grid">


            <div class="form-group">

                <label>
                    Upstream DNS 1
                </label>

                <input value="1.1.1.1">

            </div>


            <div class="form-group">

                <label>
                    Upstream DNS 2
                </label>

                <input value="8.8.8.8">

            </div>


        </div>


        <button class="button">
            Save DNS Settings
        </button>


    </form>

</div>


<!-- =========================================
     FIREWALL
     ========================================= -->

{% elif page == "firewall" %}


<div class="card">

    <div class="section-title">
        Firewall
    </div>


    <form method="POST"
          action="/save/firewall">


        <div class="setting-row">

            <span>
                Firewall
            </span>

            <div class="toggle
                {% if config.firewall_enabled %}
                    on
                {% endif %}">
            </div>

        </div>


        <div class="setting-row">

            <span>
                Block unsolicited inbound traffic
            </span>

            <div class="toggle on"></div>

        </div>


        <div class="setting-row">

            <span>
                Allow established connections
            </span>

            <div class="toggle on"></div>

        </div>


        <div class="section-title"
             style="margin-top:25px">

            Firewall Rules

        </div>


        <table>

            <tr>

                <th>
                    Direction
                </th>

                <th>
                    Protocol
                </th>

                <th>
                    Port
                </th>

                <th>
                    Action
                </th>

            </tr>


            <tr>

                <td>
                    LAN → WAN
                </td>

                <td>
                    TCP
                </td>

                <td>
                    443
                </td>

                <td class="green">
                    ALLOW
                </td>

            </tr>


            <tr>

                <td>
                    WAN → LAN
                </td>

                <td>
                    ALL
                </td>

                <td>
                    ALL
                </td>

                <td class="red">
                    BLOCK
                </td>

            </tr>

        </table>


        <button class="button">
            Save Firewall Settings
        </button>


    </form>

</div>


<!-- =========================================
     VPN
     ========================================= -->

{% elif page == "vpn" %}


<div class="card">

    <div class="section-title">
        VPN
    </div>


    <form method="POST"
          action="/save/vpn">


        <div class="setting-row">

            <span>
                VPN
            </span>

            <div class="toggle
                {% if config.vpn_enabled %}
                    on
                {% endif %}">
            </div>

        </div>


        <div class="setting-row">

            <span>
                Kill Switch
            </span>

            <div class="toggle
                {% if config.vpn_kill_switch %}
                    on
                {% endif %}">
            </div>

        </div>


        <div class="form-grid">


            <div class="form-group">

                <label>
                    VPN Configuration
                </label>

                <select>

                    <option>
                        No configuration selected
                    </option>

                </select>

            </div>


        </div>


        <button class="button">
            Save VPN Settings
        </button>


    </form>

</div>


<!-- =========================================
     MONITORING
     ========================================= -->

{% elif page == "monitoring" %}


<div class="cards">


    <div class="card">

        <div class="card-title">
            CPU Usage
        </div>

        <div class="card-value">
            --
        </div>

    </div>


    <div class="card">

        <div class="card-title">
            Memory
        </div>

        <div class="card-value">
            --
        </div>

    </div>


    <div class="card">

        <div class="card-title">
            RX Traffic
        </div>

        <div class="card-value">
            --
        </div>

    </div>


    <div class="card">

        <div class="card-title">
            TX Traffic
        </div>

        <div class="card-value">
            --
        </div>

    </div>


</div>


<div class="card">

    <div class="section-title">
        Connected Clients
    </div>


    <table>

        <tr>

            <th>
                Device
            </th>

            <th>
                IP
            </th>

            <th>
                Interface
            </th>

            <th>
                Status
            </th>

        </tr>


        <tr>

            <td>
                No clients detected
            </td>

            <td>
                --
            </td>

            <td>
                --
            </td>

            <td class="green">
                --
            </td>

        </tr>

    </table>

</div>


<!-- =========================================
     LOGS
     ========================================= -->

{% elif page == "logs" %}


<div class="card">

    <div class="section-title">
        System Logs
    </div>


    <div class="logs">

        {% for log in logs %}

            {{ log }}<br>

        {% endfor %}

    </div>

</div>


{% endif %}


</div>

</main>

</div>

</body>

</html>
"""


# ============================================================
# Start
# ============================================================

if __name__ == "__main__":
    main()
