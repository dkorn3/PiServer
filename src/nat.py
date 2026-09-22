
import subprocess

from config import load_config


def _run(command):
    """Run a system command and return the completed process."""
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )


def _get_network_settings():
    """Load WAN/LAN settings from the PiServer configuration."""
    config = load_config()
    network = config["network"]

    return {
        "wan_interface": network["wan_interface"],
        "lan_interface": network["lan_interface"],
        "lan_network": network["lan_network"],
    }


def configure_nat():
    """
    Configure IPv4 masquerading for PiServer LAN traffic.

    Traffic originating from the LAN subnet is NATed when
    leaving through the WAN interface.
    """
    settings = _get_network_settings()

    wan_interface = settings["wan_interface"]
    lan_network = settings["lan_network"]

    # Create the PiServer NAT table.
    result = _run(
        ["nft", "add", "table", "ip", "piserver_nat"]
    )

    if result.returncode != 0:
        if "exists" not in result.stderr.lower():
            raise RuntimeError(
                result.stderr.strip()
                or "Failed to create NAT table"
            )

    # Create the postrouting chain.
    result = _run(
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

    if result.returncode != 0:
        if "exists" not in result.stderr.lower():
            raise RuntimeError(
                result.stderr.strip()
                or "Failed to create NAT postrouting chain"
            )

    # Masquerade LAN traffic leaving through the WAN.
    result = _run(
        [
            "nft",
            "add",
            "rule",
            "ip",
            "piserver_nat",
            "postrouting",
            "oifname",
            wan_interface,
            "ip",
            "saddr",
            lan_network,
            "masquerade",
        ]
    )

    if result.returncode != 0:
        if "exists" not in result.stderr.lower():
            raise RuntimeError(
                result.stderr.strip()
                or "Failed to create NAT masquerade rule"
            )

    return get_nat_status()


def get_nat_status():
    """Return the current PiServer NAT configuration."""
    result = _run(
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
    result = _run(
        ["nft", "delete", "table", "ip", "piserver_nat"]
    )

    if result.returncode != 0:
        if "does not exist" in result.stderr.lower():
            return True

        raise RuntimeError(
            result.stderr.strip()
            or "Failed to disable NAT"
        )

    return True


if __name__ == "__main__":
    print("=== PiServer NAT ===")

    try:
        status = configure_nat()

        print(f"NAT enabled: {status['enabled']}")

        if status["rules"]:
            print(status["rules"])

    except (OSError, RuntimeError, ValueError) as exc:
        print(f"NAT configuration failed: {exc}")
        raise SystemExit(1)
