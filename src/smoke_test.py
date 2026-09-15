#!/usr/bin/env python3

import pprint
import monitoring
import network
import dns
import dhcp
import firewall

print("=== NETWORK ===")
pprint.pprint(network.get_network_status())

print("\n=== DNS ===")
pprint.pprint(dns.get_dns_health())

print("\n=== DHCP ===")
pprint.pprint(dhcp.get_dhcp_health())

print("\n=== FIREWALL ===")
pprint.pprint(firewall.check_firewall_integrity())

print("\n=== MONITORING ===")
pprint.pprint(monitoring.get_gateway_health())
