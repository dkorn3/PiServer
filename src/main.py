import config
import network
import dns
import dhcp
import firewall
import monitoring
import logging

try:
    import vpn
except ImportError:
    vpn = None


_running = False
_gateway_config = None


def initialize_gateway():
    global _running, _gateway_config

    _gateway_config = config.load_config()
    config.validate_config(_gateway_config)

    logging.configure_logging()
    logging.log_info("Gateway initialization started.")

    lan = _gateway_config["network"]["lan_interface"]
    wan = _gateway_config["network"]["wan_interface"]

    network.bring_interface_up(lan)
    network.configure_lan_address(
        lan,
        _gateway_config["network"]["lan_address"],
    )
    network.enable_ipv4_forwarding()

    if _gateway_config["firewall"].get("enabled", True):
        firewall.save_ruleset(lan, wan)
        firewall.apply_firewall_rules(lan, wan)

    if _gateway_config["dhcp"].get("enabled", True):
        dhcp_config = dict(_gateway_config["dhcp"])
        dhcp_config["interface"] = _gateway_config["network"]["lan_interface"]
        dhcp_config["address"] = _gateway_config["network"]["lan_address"].split("/")[0]
        dhcp.configure_dhcp(dhcp_config)

    dns.set_upstream_servers(
        _gateway_config["dns"]["upstream_servers"]
    )

    if vpn is not None and _gateway_config["vpn"].get("enabled", False):
        vpn.start()

    _running = True
    logging.log_info("Gateway initialization completed.")

    return True


def get_gateway_status():
    return {
        "running": _running,
        "config": _gateway_config,
        "health": monitoring.get_gateway_health(),
    }


def shutdown_gateway():
    global _running

    logging.log_info("Gateway shutdown started.")

    if vpn is not None:
        try:
            vpn.stop()
        except AttributeError:
            pass

    _running = False
    logging.log_info("Gateway shutdown completed.")

    return True


def main():
    initialize_gateway()

    print("PiServer gateway running.")
    print(monitoring.get_gateway_health())


if __name__ == "__main__":
    main()
