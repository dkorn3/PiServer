import subprocess
import os
import time

try:
    import psutil
except ImportError:
    psutil = None


## System Monitoring ##


def get_system_status():
    """
    Return a snapshot of overall system health.
    """
    return {
        "cpu_usage": get_cpu_usage(),
        "memory_usage": get_memory_usage(),
        "storage_usage": get_storage_usage(),
        "temperature": get_temperature(),
        "uptime": get_uptime(),
    }


def get_cpu_usage():
    """
    Return CPU utilization as a percentage.
    """
    if psutil is None:
        return None

    return psutil.cpu_percent(interval=0.5)


def get_memory_usage():
    """
    Return memory utilization as a percentage.
    """
    if psutil is None:
        return None

    return psutil.virtual_memory().percent


def get_storage_usage():
    """
    Return root filesystem storage utilization as a percentage.
    """
    if psutil is None:
        return None

    return psutil.disk_usage("/").percent


def get_temperature():
    """
    Return CPU/system temperature in degrees Celsius.

    Raspberry Pi Linux systems commonly expose thermal data through:
        /sys/class/thermal/thermal_zone0/temp
    """
    temperature_file = "/sys/class/thermal/thermal_zone0/temp"

    try:
        with open(temperature_file, "r") as file:
            temperature = int(file.read().strip())

        return temperature / 1000.0

    except (FileNotFoundError, ValueError, OSError):
        return None


def get_uptime():
    """
    Return system uptime in seconds.
    """
    if psutil is not None:
        return time.time() - psutil.boot_time()

    try:
        with open("/proc/uptime", "r") as file:
            return float(file.read().split()[0])

    except (FileNotFoundError, ValueError, OSError):
        return None


## Network Monitoring ##


def get_interface_stats(interface):
    """
    Return traffic and error statistics for a network interface.
    """
    if psutil is None:
        return None

    stats = psutil.net_io_counters(pernic=True)

    if interface not in stats:
        return None

    interface_stats = stats[interface]

    return {
        "bytes_sent": interface_stats.bytes_sent,
        "bytes_received": interface_stats.bytes_recv,
        "packets_sent": interface_stats.packets_sent,
        "packets_received": interface_stats.packets_recv,
        "errors_sent": interface_stats.errout,
        "errors_received": interface_stats.errin,
        "drops_sent": interface_stats.dropout,
        "drops_received": interface_stats.dropin,
    }


def get_network_stats():
    """
    Return statistics for all available network interfaces.
    """
    if psutil is None:
        return {}

    stats = psutil.net_io_counters(pernic=True)

    return {
        interface: {
            "bytes_sent": interface_stats.bytes_sent,
            "bytes_received": interface_stats.bytes_recv,
            "packets_sent": interface_stats.packets_sent,
            "packets_received": interface_stats.packets_recv,
            "errors_sent": interface_stats.errout,
            "errors_received": interface_stats.errin,
            "drops_sent": interface_stats.dropout,
            "drops_received": interface_stats.dropin,
        }
        for interface, interface_stats in stats.items()
    }


def get_connection_count():
    """
    Return the number of active TCP connections.

    psutil.net_connections() requires appropriate privileges for
    complete system-wide results.
    """
    if psutil is None:
        return None

    try:
        connections = psutil.net_connections(kind="tcp")
        return len(connections)

    except (psutil.AccessDenied, OSError):
        return None


## Service Monitoring ##


def get_service_status(service):
    """
    Return the systemd state of a service.

    Example:
        get_service_status("ssh")
    """
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service],
            capture_output=True,
            text=True,
            check=False
        )

        return result.stdout.strip()

    except OSError:
        return None


def get_gateway_services_status():
    """
    Return the status of the services used by the gateway.

    These names are placeholders until the actual service layout
    is finalized.
    """
    services = {
        "ssh": "ssh",
        "wireguard": "wg-quick@wg0",
    }

    return {
        name: get_service_status(service)
        for name, service in services.items()
    }


## VPN Monitoring ##


def get_vpn_status():
    """
    Return the operational state of WireGuard.
    """
    try:
        result = subprocess.run(
            ["wg", "show", "wg0"],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            return "inactive"

        return "active"

    except OSError:
        return "unknown"


def get_vpn_handshake():
    """
    Return WireGuard peer handshake information.

    The result is a dictionary keyed by peer public key.
    """
    try:
        result = subprocess.run(
            ["wg", "show", "wg0", "latest-handshakes"],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            return {}

        handshakes = {}

        for line in result.stdout.splitlines():
            parts = line.split()

            if len(parts) != 2:
                continue

            public_key = parts[0]

            try:
                timestamp = int(parts[1])
            except ValueError:
                timestamp = None

            handshakes[public_key] = timestamp

        return handshakes

    except OSError:
        return {}


def get_vpn_statistics():
    """
    Return WireGuard transfer statistics for each peer.
    """
    try:
        result = subprocess.run(
            ["wg", "show", "wg0", "transfer"],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            return {}

        statistics = {}

        for line in result.stdout.splitlines():
            parts = line.split()

            if len(parts) != 3:
                continue

            public_key = parts[0]

            try:
                received = int(parts[1])
                sent = int(parts[2])
            except ValueError:
                continue

            statistics[public_key] = {
                "bytes_received": received,
                "bytes_sent": sent,
            }

        return statistics

    except OSError:
        return {}


## DNS Monitoring ##

def get_dns_health():
    """
    Return DNS health information.

    The DNS module owns DNS-specific behavior; this function
    provides a monitoring interface for it.
    """
    try:
        import dns

        return dns.get_dns_health()

    except (ImportError, AttributeError):
        return {
            "status": "unknown",
            "reason": "DNS monitoring not implemented",
        }


## DHCP Monitoring ##


def get_dhcp_health():
    """
    Return DHCP health information.
    """
    try:
        import dhcp

        return dhcp.get_dhcp_health()

    except (ImportError, AttributeError):
        return {
            "status": "unknown",
            "reason": "DHCP monitoring not implemented",
        }


## Firewall Monitoring ##


def get_firewall_health():
    """
    Return firewall health information.
    """
    try:
        import firewall

        status = firewall.get_firewall_status()

        return {
            "status": status
        }

    except (ImportError, AttributeError):
        return {
            "status": "unknown",
            "reason": "Firewall monitoring not implemented",
        }


## Gateway Health ##


def get_gateway_health():
    """
    Return a combined health snapshot of the gateway.
    """
    return {
        "system": get_system_status(),
        "network": get_network_stats(),
        "connections": get_connection_count(),
        "services": get_gateway_services_status(),
        "vpn": {
            "status": get_vpn_status(),
            "handshakes": get_vpn_handshake(),
            "statistics": get_vpn_statistics(),
        },
        "dns": get_dns_health(),
        "dhcp": get_dhcp_health(),
        "firewall": get_firewall_health(),
    }
