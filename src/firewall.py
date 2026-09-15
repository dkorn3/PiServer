import subprocess
import tempfile

TABLE_FAMILY = "inet"
TABLE_NAME = "pi_gateway"
RULESET_PATH = "/etc/nftables.d/pi-gateway.nft"

RULE_TEMPLATE = """table inet pi_gateway {{
    chain forward {{
        type filter hook forward priority 0; policy drop;

        ct state established,related accept
        ct state invalid drop

        iifname "{lan}" oifname "{wan}" accept
    }}

    chain input {{
        type filter hook input priority 0; policy accept;

        ct state invalid drop
    }}

    chain output {{
        type filter hook output priority 0; policy accept;
    }}
}}
"""


def _run(command):
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )


def get_firewall_status():
    result = _run(["nft", "list", "table", TABLE_FAMILY, TABLE_NAME])

    if result.returncode == 0:
        return "active"

    return "inactive"


def get_firewall_rules():
    result = _run(["nft", "list", "table", TABLE_FAMILY, TABLE_NAME])

    if result.returncode != 0:
        return []

    return result.stdout.splitlines()


def validate_firewall_rules():
    result = _run(["nft", "-c", "-f", RULESET_PATH])

    return {
        "valid": result.returncode == 0,
        "output": result.stderr.strip() or result.stdout.strip(),
    }


def apply_firewall_rules(lan_interface="eth1", wan_interface="wlan0"):
    ruleset = RULE_TEMPLATE.format(
        lan=lan_interface,
        wan=wan_interface,
    )

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".nft",
        delete=False,
    ) as file:
        file.write(ruleset)
        temp_path = file.name

    try:
        check = _run(["nft", "-c", "-f", temp_path])

        if check.returncode != 0:
            return False

        result = _run(["nft", "-f", temp_path])

        if result.returncode != 0:
            return False

        return True

    finally:
        try:
            subprocess.run(["rm", "-f", temp_path], check=False)
        except OSError:
            pass


def reload_firewall():
    result = _run(["nft", "list", "ruleset"])

    if result.returncode != 0:
        return False

    result = _run(["systemctl", "reload", "nftables"])

    return result.returncode == 0


def _get_counter_lines():
    result = _run(["nft", "-a", "list", "table", TABLE_FAMILY, TABLE_NAME])

    if result.returncode != 0:
        return []

    return result.stdout.splitlines()


def get_blocked_connections():
    return [
        line.strip()
        for line in _get_counter_lines()
        if "drop" in line.lower()
    ]


def get_allowed_connections():
    return [
        line.strip()
        for line in _get_counter_lines()
        if "accept" in line.lower()
    ]


def get_firewall_counters():
    lines = _get_counter_lines()

    return {
        "rule_lines": len(lines),
        "accept_rules": sum(" accept" in line for line in lines),
        "drop_rules": sum(" drop" in line for line in lines),
    }


def check_firewall_integrity():
    status = get_firewall_status()

    return {
        "status": "healthy" if status == "active" else "failed",
        "rules_loaded": status == "active",
        "table": f"{TABLE_FAMILY} {TABLE_NAME}",
    }


def test_firewall():
    result = _run(["nft", "list", "ruleset"])

    return {
        "success": result.returncode == 0,
        "output": result.stderr.strip() or result.stdout.strip(),
    }


def save_ruleset(lan_interface="eth1", wan_interface="wlan0"):
    ruleset = RULE_TEMPLATE.format(
        lan=lan_interface,
        wan=wan_interface,
    )

    with open(RULESET_PATH, "w", encoding="utf-8") as file:
        file.write(ruleset)

    return RULESET_PATH
