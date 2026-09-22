
import subprocess


WAN_INTERFACE = "eth0"
LAN_INTERFACE = "wlan0"
LAN_SUBNET = "192.168.50.0/24"


def run_command(command):
    """Run a system command and return the result."""
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )


def configure_nat():
    """Configure NAT for traffic from the PiServer LAN."""

    # Create NAT table.
    result = run_command(
        ["nft", "add", "table", "ip", "piserver_nat"]
    )

    if result.returncode != 0 and "exists" not in result.stderr.lower():
        raise RuntimeError(
            result.stderr.strip() or "Failed to create NAT table"
        )

    # Create postrouting chain.
    result = run_command(
        [
            "nft",
            "add",
            "chain",
            "ip",
            "piserver_nat",
            "postrouting",
            "{",
            "type",
            "nat",
            "hook",
            "postrouting",
            "priority",
            "100",
            ";",
            "policy",
            "accept",
            ";",
            "}",
        ]
    )

    if result.returncode != 0 and "exists" not in result.stderr.lower():
        raise RuntimeError(
            result.stderr.strip() or "Failed to create NAT chain"
        )

    # Masquerade PiServer LAN traffic leaving through eth0.
    result = run_command(
        [
            "nft",
            "add",
            "rule",
            "ip",
            "piserver_nat",
            "postrouting",
            "oifname",
            WAN_INTERFACE,
            "ip",
            "saddr",
            LAN_SUBNET,
            "masquerade",
        ]
    )

    if result.returncode != 0 and "exists" not in result.stderr.lower():
        raise RuntimeError(
            result.stderr.strip() or "Failed to create NAT rule"
        )

    return True


def get_nat_status():
    """Return the current PiServer NAT configuration."""

    result = run_command(
        ["nft", "list", "table", "ip", "piserver_nat"]
    )

    return {
        "enabled": result.returncode == 0,
        "rules": result.stdout.strip(),
        "error": (
            result.stderr.strip()
            if result.returncode != 0
            else None
        ),
    }


def disable_nat():
    """Remove the PiServer NAT table."""

    result = run_command(
        ["nft", "delete", "table", "ip", "piserver_nat"]
    )

    if result.returncode != 0:
        if "does not exist" in result.stderr.lower():
            return True

        raise RuntimeError(
            result.stderr.strip() or "Failed to disable NAT"
        )

    return True


if __name__ == "__main__":
    print("=== PiServer NAT ===")

    try:
        configure_nat()

        status = get_nat_status()

        print(f"NAT enabled: {status['enabled']}")
        print(status["rules"])

    except RuntimeError as error:
        print(f"NAT configuration failed: {error}")
