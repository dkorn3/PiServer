
from flask import Flask, request, redirect, url_for, render_template_string, jsonify
from datetime import datetime
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
    "hostname": _BOOT_CONFIG.get("hostname", "PiServer"),

    # WAN interface
    "interface": _BOOT_NETWORK.get(
        "wan_interface",
        "eth0"
    ),

    # Gateway mode
    "mode": "gateway",

    # LAN address
    "ip_address": (
        _BOOT_NETWORK.get(
            "lan_address",
            ""
        ).split("/")[0]
    ),

    # Upstream gateway
    "gateway": "",

    # LAN netmask
    "netmask": "255.255.255.0",

    # DNS server
    "dns": (
        _BOOT_DNS.get(
            "upstream_servers",
            ["1.1.1.1"]
        )[0]
        if _BOOT_DNS
        else "1.1.1.1"
    ),

    # Services
    "dhcp_enabled": _BOOT_DHCP.get(
        "enabled",
        True
    ),

    "dns_enabled": _BOOT_DNS.get(
        "enabled",
        False
    ),

    "firewall_enabled": _BOOT_FIREWALL.get(
        "enabled",
        False
    ),

    "vpn_enabled": _BOOT_VPN.get(
        "enabled",
        False
    ),

    # NAT
    "nat_enabled": _BOOT_NETWORK.get(
        "nat_enabled",
        False
    ),
}


LOGS = []


# ============================================================
# Configuration functions
# ============================================================

def _current_backend_config():
    """
    Translate the GUI configuration into the PiServer
    gateway configuration.
    """

    cfg = gateway_config.load_config()

    # Hostname
    cfg["hostname"] = CONFIG["hostname"]

    # WAN
    cfg["network"]["wan_interface"] = CONFIG["interface"]

    # LAN
    cfg["network"]["lan_interface"] = cfg[
        "network"
    ].get(
        "lan_interface",
        "wlan0"
    )

    # LAN address
    if CONFIG["ip_address"]:
        # CONFIG["netmask"] is currently a dotted
        # decimal netmask such as 255.255.255.0.
        #
        # ip_interface() expects CIDR notation,
        # so convert the netmask to a prefix length.
        import ipaddress

        try:
            prefix = ipaddress.IPv4Network(
                f"0.0.0.0/{CONFIG['netmask']}"
            ).prefixlen
        except ValueError:
            prefix = 24

        cfg["network"]["lan_address"] = (
            f'{CONFIG["ip_address"]}/{prefix}'
        )

        # Keep the LAN network consistent with
        # the LAN address.
        cfg["network"]["lan_network"] = str(
            ipaddress.ip_interface(
                cfg["network"]["lan_address"]
            ).network
        )

    # NAT
    cfg["network"]["nat_enabled"] = CONFIG[
        "nat_enabled"
    ]

    # DHCP
    cfg["dhcp"]["enabled"] = CONFIG[
        "dhcp_enabled"
    ]

    # DNS
    cfg["dns"]["enabled"] = CONFIG[
        "dns_enabled"
    ]

    # Firewall
    cfg["firewall"]["enabled"] = CONFIG[
        "firewall_enabled"
    ]

    # VPN
    cfg["vpn"]["enabled"] = CONFIG[
        "vpn_enabled"
    ]

    return cfg


def configure_network():
    """
    Save the current GUI configuration.
    """

    cfg = _current_backend_config()

    gateway_config.save_config(cfg)

    gateway_logging.log_info(
        "Network configuration updated."
    )

    return True


def configure_nat():
    """
    Enable or disable IPv4 NAT according to the
    current GUI configuration.
    """

    if CONFIG["nat_enabled"]:

        try:
            status = nat_backend.configure_nat()

            success = status.get(
                "enabled",
                False
            )

        except Exception as exc:

            gateway_logging.log_info(
                f"NAT configuration failed: {exc}"
            )

            return False

    else:

        try:
            nat_backend.disable_nat()
            success = True

        except Exception as exc:

            gateway_logging.log_info(
                f"NAT disable failed: {exc}"
            )

            return False

    gateway_logging.log_info(
        "NAT enabled."
        if CONFIG["nat_enabled"]
        else "NAT disabled."
    )

    return success


def configure_dhcp():
    """
    Configure the DHCP service.
    """

    cfg = _current_backend_config()

    dhcp_cfg = dict(
        cfg["dhcp"]
    )

    dhcp_cfg["interface"] = cfg[
        "network"
    ]["lan_interface"]

    dhcp_cfg["address"] = cfg[
        "network"
    ]["lan_address"].split("/")[0]

    if CONFIG["dhcp_enabled"]:

        success = dhcp_backend.configure_dhcp(
            dhcp_cfg
        )

    else:

        import subprocess

        result = subprocess.run(
            [
                "systemctl",
                "stop",
                "dnsmasq"
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        success = (
            result.returncode == 0
        )

    gateway_logging.log_info(
        "DHCP configuration applied."
        if success
        else "DHCP configuration failed."
    )

    return success


def configure_dns():
    """
    Configure the DNS service.
    """

    cfg = _current_backend_config()

    servers = cfg[
        "dns"
    ]["upstream_servers"]

    if not CONFIG["dns_enabled"]:

        import subprocess

        result = subprocess.run(
            [
                "systemctl",
                "stop",
                "dnsmasq"
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        success = (
            result.returncode == 0
        )

    else:

        dns_backend.set_upstream_servers(
            servers
        )

        success = True

    gateway_logging.log_info(
        "DNS configuration updated."
        if success
        else "DNS configuration failed."
    )

    return success


def configure_firewall():
    """
    Configure the firewall.
    """

    cfg = _current_backend_config()

    lan = cfg[
        "network"
    ]["lan_interface"]

    wan = cfg[
        "network"
    ]["wan_interface"]

    if not CONFIG["firewall_enabled"]:

        import subprocess

        result = subprocess.run(
            [
                "systemctl",
                "stop",
                "nftables"
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        success = (
            result.returncode == 0
        )

    else:

        firewall_backend.save_ruleset(
            lan,
            wan
        )

        success = (
            firewall_backend.apply_firewall_rules(
                lan,
                wan
            )
        )

    gateway_logging.log_info(
        "Firewall configuration updated."
        if success
        else "Firewall configuration failed."
    )

    return success


def configure_vpn():
    """
    VPN configuration placeholder.

    WireGuard integration can be connected here later.
    """

    gateway_logging.log_info(
        "VPN configuration toggle updated."
    )

    return True


def update_monitoring():
    return monitoring.get_gateway_health()


def update_network_status():
    """
    Return the live Linux network state for
    the Network page.
    """

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

        gateway_logging.log_info(
            message
        )

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

@app.route(
    "/network",
    methods=["GET", "POST"]
)
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

        # NAT checkbox
        CONFIG["nat_enabled"] = (
            request.form.get(
                "nat_enabled"
            ) == "on"
        )

        # Save configuration
        configure_network()

        # Apply NAT
        configure_nat()

        add_log(
            "Network configuration updated."
        )

        return redirect(
            url_for("network")
        )

    network_status = (
        update_network_status()
    )

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

@app.route(
    "/dhcp",
    methods=["GET", "POST"]
)
def dhcp():

    if request.method == "POST":

        CONFIG["dhcp_enabled"] = (
            request.form.get(
                "dhcp_enabled"
            ) == "on"
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

        return redirect(
            url_for("dhcp")
        )

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

@app.route(
    "/dns",
    methods=["GET", "POST"]
)
def dns():

    if request.method == "POST":

        CONFIG["dns_enabled"] = (
            request.form.get(
                "dns_enabled"
            ) == "on"
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

        return redirect(
            url_for("dns")
        )

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

@app.route(
    "/firewall",
    methods=["GET", "POST"]
)
def firewall():

    if request.method == "POST":

        CONFIG["firewall_enabled"] = (
            request.form.get(
                "firewall_enabled"
            ) == "on"
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

        return redirect(
            url_for("firewall")
        )

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

@app.route(
    "/vpn",
    methods=["GET", "POST"]
)
def vpn():

    if request.method == "POST":

        CONFIG["vpn_enabled"] = (
            request.form.get(
                "vpn_enabled"
            ) == "on"
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

        return redirect(
            url_for("vpn")
        )

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

**Keep your existing `HTML = """ ... """` section exactly as it is** and place it between the `/logs` route and `# Main` section above.

One additional change is needed in your **Network HTML** if you want the NAT toggle to appear. Inside the `/network` form, add:

```html
<div class="toggle-row">

    <div>
        <strong>
            NAT / Internet Sharing
        </strong>

        <div class="info-label">
            Masquerade LAN traffic through the WAN interface
        </div>
    </div>

    <label class="toggle-switch">

        <input
            type="checkbox"
            name="nat_enabled"
            {% if config.nat_enabled %}
            checked
            {% endif %}
        >

        <span class="slider"></span>

    </label>

</div>
```

Then your flow becomes:

```text
Browser
   ↓
network_gui.py
   ↓
configure_nat()
   ↓
nat.py
   ↓
nft
   ↓
Linux NAT
```

And your configuration is persisted through:

```text
GUI
 ↓
gateway.yaml
 ↓
nat_enabled: true
