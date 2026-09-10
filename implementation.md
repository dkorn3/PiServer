sudo apt install python3-flask
sudo apt install python3-psutil -y

sudo nano /etc/systemd/system/pi-gateway.service

[Unit]
Description=Raspberry Pi Network Gateway GUI
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/(your Pi Username)/PiServer/src
ExecStart=/usr/bin/python3 /home/dominikkornak/PiServer/src/network_gui.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target

sudo systemctl daemon-reload
sudo systemctl enable pi-gateway
sudo systemctl start pi-gateway


## Phase 1 — Base Linux System

[ ] Install Linux on Raspberry Pi 3
[ ] Configure hostname
[ ] Configure timezone
[ ] Update system packages
[ ] Configure SSH
[ ] Create dedicated administrative user
[ ] Disable unnecessary services
[ ] Configure automatic security updates
[ ] Configure persistent storage
[ ] Verify system boots reliably
[ ] Verify CPU, memory, storage, and temperature monitoring

## Phase 2 — Network Interfaces

### WAN

[ ] Identify Wi-Fi interface
[ ] Configure Wi-Fi connection
[ ] Configure WAN DHCP
[ ] Verify WAN IP assignment
[ ] Verify WAN default route
[ ] Verify gateway can reach the Internet

### LAN

[ ] Identify USB Ethernet interface
[ ] Configure LAN interface
[ ] Assign 192.168.50.1/24
[ ] Verify LAN interface remains static
[ ] Connect test client
[ ] Verify client can reach 192.168.50.1

### Routing

[ ] Enable IPv4 forwarding
[ ] Verify kernel routing
[ ] Verify LAN → WAN forwarding
[ ] Verify return traffic
[ ] Verify routing survives reboot

## Phase 3 — DHCP

[ ] Install/configure DHCP service
[ ] Configure LAN DHCP range
[ ] Configure 192.168.50.100 - 192.168.50.200
[ ] Advertise 192.168.50.1 as default gateway
[ ] Advertise 192.168.50.1 as DNS server
[ ] Test DHCP lease acquisition
[ ] Test lease renewal
[ ] Test multiple clients
[ ] Test DHCP after reboot
[ ] Implement optional static DHCP reservations

## Phase 4 — DNS

[ ] Install/configure DNS forwarding service
[ ] Configure LAN clients to use gateway DNS
[ ] Configure upstream DNS servers
[ ] Test normal DNS resolution
[ ] Test DNS failure handling
[ ] Prevent LAN clients from directly using unauthorized DNS servers
[ ] Test UDP DNS enforcement
[ ] Test TCP DNS enforcement
[ ] Implement DNS logging
[ ] Implement configurable DNS settings
[ ] Implement DNS health monitoring

### Later

[ ] Domain blocklists
[ ] Malware-domain blocking
[ ] Advertisement/tracker blocking
[ ] Local DNS records
[ ] Per-client DNS policies

## Phase 5 — Firewall

[ ] Install/configure nftables
[ ] Create LAN zone
[ ] Create WAN zone
[ ] Create default-deny policy
[ ] Allow required LAN → WAN traffic
[ ] Allow established connections
[ ] Allow related connections
[ ] Drop invalid traffic
[ ] Block unsolicited WAN → LAN traffic
[ ] Block unauthorized LAN → gateway traffic
[ ] Allow required DHCP traffic
[ ] Allow required DNS traffic
[ ] Allow required management traffic
[ ] Configure firewall logging
[ ] Test every major firewall rule
[ ] Test firewall persistence after reboot

### Security Tests

[ ] Scan gateway from WAN
[ ] Verify management ports aren't exposed
[ ] Attempt WAN → LAN connection
[ ] Attempt LAN client → LAN client connection
[ ] Verify established return traffic works
[ ] Verify invalid traffic is blocked

## Phase 6 — NAT

[ ] Configure LAN → WAN masquerading
[ ] Verify private LAN addresses are translated
[ ] Test TCP connections through NAT
[ ] Test UDP connections through NAT
[ ] Test multiple LAN clients simultaneously
[ ] Verify connection tracking
[ ] Test NAT after reboot
[ ] Verify firewall remains the actual security boundary

## Phase 7 — WireGuard

[ ] Install WireGuard
[ ] Generate gateway private/public key pair
[ ] Configure VPN server peer
[ ] Configure wg0
[ ] Assign VPN tunnel address
[ ] Configure VPN endpoint
[ ] Configure AllowedIPs
[ ] Establish WireGuard handshake
[ ] Verify encrypted traffic
[ ] Verify traffic through VPN
[ ] Verify VPN public IP differs from WAN public IP
[ ] Configure persistent keepalive if required
[ ] Configure WireGuard to start automatically
[ ] Verify VPN survives reboot

## Phase 8 — VPN Kill Switch

[ ] Prevent normal LAN traffic from bypassing VPN
[ ] Allow required WireGuard endpoint traffic through WAN
[ ] Allow LAN traffic through wg0
[ ] Block LAN → WAN Internet traffic when VPN is unavailable
[ ] Prevent DNS from bypassing VPN
[ ] Test VPN disconnect
[ ] Test WAN connectivity while VPN is down
[ ] Verify protected LAN has no Internet while VPN is down
[ ] Restore VPN
[ ] Verify Internet automatically returns
[ ] Test VPN reconnect
[ ] Test behavior after gateway reboot
[ ] Test behavior when WAN temporarily disappears

### IPv6

[ ] Determine IPv6 requirements
[ ] Prevent IPv6 VPN bypass
[ ] Either implement IPv6 VPN routing or block IPv6 while VPN enforcement is active
[ ] Test for IPv6 leaks

## Phase 9 — Network Isolation

[ ] Implement LAN client isolation
[ ] Test client → client connectivity
[ ] Block unauthorized client-to-client traffic
[ ] Protect gateway management services
[ ] Restrict SSH access
[ ] Define management access policy
[ ] Verify WAN cannot access management
[ ] Verify WAN cannot access LAN
[ ] Verify LAN access to gateway follows policy

### Future Segmentation

[ ] Design VLAN architecture
[ ] Implement Management zone
[ ] Implement Guest zone
[ ] Implement IoT zone
[ ] Create inter-zone firewall policies
[ ] Test lateral-movement restrictions

## Phase 10 — Monitoring

[ ] Monitor LAN interface
[ ] Monitor WAN interface
[ ] Monitor wg0
[ ] Monitor interface traffic
[ ] Monitor packet counts
[ ] Monitor connection counts
[ ] Monitor CPU
[ ] Monitor memory
[ ] Monitor storage
[ ] Monitor temperature
[ ] Monitor system uptime
[ ] Monitor service status
[ ] Monitor VPN handshake
[ ] Monitor VPN reconnect attempts
[ ] Monitor DNS health
[ ] Monitor DHCP status

## Phase 11 — Logging

[ ] Configure system logging
[ ] Configure firewall logs
[ ] Configure DNS logs
[ ] Configure VPN logs
[ ] Configure authentication logs
[ ] Configure configuration-change logs
[ ] Implement log rotation
[ ] Implement log retention limits
[ ] Prevent logs from filling storage
[ ] Add log filtering
[ ] Add log severity levels
[ ] Test log persistence/recovery

## Phase 12 — Management Layer

### Configuration

[ ] Define central configuration format
[ ] Define network configuration schema
[ ] Define firewall configuration schema
[ ] Define DNS configuration schema
[ ] Define DHCP configuration schema
[ ] Define VPN configuration schema
[ ] Define security-policy schema

### Configuration Engine

[ ] Build configuration parser
[ ] Validate configuration
[ ] Detect invalid configurations
[ ] Apply configuration changes
[ ] Safely reload affected services
[ ] Roll back failed configuration changes
[ ] Persist configuration

### CLI

[ ] Create gateway CLI
[ ] Show system status
[ ] Show interface status
[ ] Show connected clients
[ ] Show firewall status
[ ] Show VPN status
[ ] Show DNS status
[ ] Show DHCP status
[ ] Modify configuration
[ ] Apply configuration
[ ] View logs

### Web UI — Later

[ ] Design dashboard
[ ] Implement authentication
[ ] Implement system-status page
[ ] Implement network configuration
[ ] Implement firewall configuration
[ ] Implement VPN configuration
[ ] Implement DNS configuration
[ ] Implement DHCP configuration
[ ] Implement client/device view
[ ] Implement logs
[ ] Implement security alerts

## Phase 13 — Security Hardening

[ ] Minimize installed packages
[ ] Disable unnecessary services
[ ] Restrict listening ports
[ ] Harden SSH
[ ] Protect configuration files
[ ] Protect WireGuard private keys
[ ] Protect management credentials
[ ] Implement file permissions
[ ] Review firewall rules
[ ] Review exposed services
[ ] Review logging for sensitive information
[ ] Test unauthorized administrative access
[ ] Test configuration tampering
[ ] Document remaining attack surface

## Phase 14 — Testing

### Functional Testing

[ ] Client obtains DHCP address
[ ] Client reaches gateway
[ ] Client resolves DNS
[ ] Client reaches Internet
[ ] NAT works
[ ] Firewall works
[ ] VPN works
[ ] Kill switch works
[ ] Management works
[ ] Logging works
[ ] Monitoring works

### Failure Testing

[ ] WAN disconnect
[ ] WAN reconnect
[ ] VPN disconnect
[ ] VPN reconnect
[ ] DNS server failure
[ ] DHCP service failure
[ ] Firewall service failure
[ ] Gateway reboot
[ ] Unexpected power loss
[ ] Invalid configuration
[ ] Storage nearly full

### Security Testing

[ ] WAN port scan
[ ] LAN port scan
[ ] Client-to-client scan
[ ] DNS leak test
[ ] VPN leak test
[ ] IPv6 leak test
[ ] Unauthorized management test
[ ] Firewall bypass attempts
[ ] Network isolation tests

## Phase 15 — Performance Benchmarking

[ ] Measure baseline routing throughput
[ ] Measure NAT throughput
[ ] Measure firewall throughput
[ ] Measure VPN throughput
[ ] Measure DNS performance
[ ] Measure maximum concurrent connections
[ ] Measure packet-per-second performance
[ ] Measure latency
[ ] Measure CPU utilization
[ ] Measure RAM utilization
[ ] Measure temperature
[ ] Measure power consumption
[ ] Test sustained load
[ ] Identify bottlenecks
[ ] Document results

### Hardware Upgrade Decision

[ ] Identify Pi 3 bottlenecks
[ ] Calculate required CPU performance
[ ] Calculate required RAM
[ ] Calculate required network bandwidth
[ ] Calculate required USB/network interfaces
[ ] Calculate thermal requirements
[ ] Calculate power requirements
[ ] Define final hardware requirements
[ ] Select next hardware platform
[ ] Re-run benchmark suite
[ ] Compare prototype vs upgraded hardware

# Milestones

[ ] Milestone 1 — Linux gateway boots
[ ] Milestone 2 — Host receives DHCP and reaches gateway
[ ] Milestone 3 — Host reaches Internet through NAT
[ ] Milestone 4 — Firewall security boundary works
[ ] Milestone 5 — DNS enforcement works
[ ] Milestone 6 — WireGuard works
[ ] Milestone 7 — VPN kill switch works
[ ] Milestone 8 — Network isolation works
[ ] Milestone 9 — Monitoring/logging works
[ ] Milestone 10 — Custom management layer works
[ ] Milestone 11 — Security testing passes
[ ] Milestone 12 — Performance benchmark complete
[ ] Milestone 13 — Hardware requirements established
