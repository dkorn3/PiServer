import os
import yaml

CONFIG_FILE = "config/gateway.yaml"

DEFAULT_CONFIG = {
    "hostname": "DomPi",
    "network": {
        "wan_interface": "wlan0",
        "lan_interface": "eth1",
        "lan_address": "192.168.50.1/24",
        "lan_network": "192.168.50.0/24",
        "wan_dhcp": True,
    },
    "firewall": {
        "enabled": True,
        "client_isolation": False,
    },
    "dns": {
        "enabled": True,
        "upstream_servers": ["1.1.1.1", "9.9.9.9"],
        "allowlist": [],
        "blocklist": [],
    },
    "dhcp": {
        "enabled": True,
        "range_start": "192.168.50.100",
        "range_end": "192.168.50.200",
        "lease_time": "12h",
    },
    "vpn": {
        "enabled": False,
        "interface": "wg0",
        "config_file": "/etc/wireguard/wg0.conf",
    },
}


def _deep_merge(base, override):
    result = dict(base)

    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def load_config():
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return _deep_merge(DEFAULT_CONFIG, {})

    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        loaded = yaml.safe_load(file) or {}

    config = _deep_merge(DEFAULT_CONFIG, loaded)
    validate_config(config)
    return config


def save_config(config):
    validate_config(config)

    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

    temp_file = CONFIG_FILE + ".tmp"

    with open(temp_file, "w", encoding="utf-8") as file:
        yaml.safe_dump(config, file, sort_keys=False)

    os.replace(temp_file, CONFIG_FILE)
    return True


def validate_config(config):
    if not isinstance(config, dict):
        raise ValueError("Configuration must be a dictionary.")

    required = {"network", "firewall", "dns", "dhcp", "vpn"}

    missing = required - set(config)
    if missing:
        raise ValueError(f"Missing configuration sections: {sorted(missing)}")

    network = config["network"]

    for key in ("wan_interface", "lan_interface", "lan_address", "lan_network"):
        if not network.get(key):
            raise ValueError(f"Missing network setting: {key}")

    if not isinstance(config["dns"].get("upstream_servers"), list):
        raise ValueError("dns.upstream_servers must be a list.")

    return True


def get_network_config(config):
    return config["network"]


def get_firewall_config(config):
    return config["firewall"]


def get_dns_config(config):
    return config["dns"]


def get_dhcp_config(config):
    return config["dhcp"]


def get_vpn_config(config):
    return config["vpn"]
