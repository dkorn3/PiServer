# Portable Security Gateway

## 1. System Overview

The Portable Security Gateway is a Linux-based network security appliance that
creates a trusted network boundary between a host device and an untrusted
network.

The gateway will route traffic between a protected LAN and an untrusted WAN.
It will provide firewalling, NAT, DNS control, VPN connectivity, and network
monitoring.

The initial prototype will use a Raspberry Pi 3 running Linux.

### High-Level Architecture

                    UNTRUSTED NETWORK
                           │
                           │ Wi-Fi
                           ▼
                  ┌─────────────────┐
                  │   Raspberry Pi  │
                  │                 │
                  │ Security        │
                  │ Gateway         │
                  │                 │
                  │ Linux           │
                  │ Routing         │
                  │ NAT             │
                  │ Firewall        │
                  │ DNS             │
                  │ WireGuard       │
                  │ Monitoring      │
                  └────────┬────────┘
                           │
                     USB Ethernet
                           │
                           ▼
                         HOST
    ## 2. Network Interfaces

The gateway will separate the network into two distinct interfaces:

### WAN Interface

The WAN interface connects the gateway to an untrusted upstream network.

For the initial prototype:

- Interface: Wi-Fi
- Purpose: Upstream Internet connectivity
- Trust level: Untrusted
- Addressing: Assigned by the upstream network using DHCP

The gateway must treat the WAN as an untrusted network and must not
allow unsolicited connections from the WAN to the protected LAN.

### LAN Interface

The LAN interface connects the gateway to protected host devices.

For the initial prototype:

- Interface: USB Ethernet
- Purpose: Connection to protected host devices
- Trust level: Trusted
- Addressing: Static gateway address with DHCP provided to clients
- Network: `192.168.50.0/24`
- Gateway: `192.168.50.1`

### Traffic Flow

Normal Internet traffic will follow this path:

    Host
      │
      │ LAN
      ▼
    Gateway
      │
      │ Routing / Firewall / NAT
      ▼
    WAN
      │
      ▼
    Internet

Traffic returning from the Internet will follow the reverse path:

    Internet
       │
       ▼
      WAN
       │
       ▼
    Gateway
       │
       │ Firewall / Connection Tracking
       ▼
      LAN
       │
       ▼
      Host     
### Network Trust Boundary

The gateway represents the security boundary between the protected LAN
and the untrusted WAN.

The gateway will:

1. Accept traffic from protected LAN clients according to firewall policy.
2. Route permitted traffic toward the WAN.
3. Perform NAT for permitted Internet-bound traffic.
4. Track connections and permit valid return traffic.
5. Block unsolicited inbound WAN traffic to the LAN.
6. Prevent the WAN from directly accessing protected LAN clients.  

## 3. Routing and NAT

### Routing

The gateway will operate as an IPv4 Layer-3 router.

The gateway will maintain separate LAN and WAN interfaces and will
forward packets between them according to its routing table.

The LAN interface will use:

- Address: `192.168.50.1/24`
- Network: `192.168.50.0/24`

The WAN interface will obtain its network configuration from the
upstream network using DHCP.

The gateway will use the upstream network's default gateway as its
default route to the Internet.

### Default Route

Internet-bound traffic from protected LAN clients will follow this path:

    Host
      │
      │ Destination: Internet
      ▼
    192.168.50.1
      │
      │ Gateway routing table
      ▼
    WAN default route
      │
      ▼
    Internet

The host will use `192.168.50.1` as its default gateway.

### Network Address Translation

The gateway will perform Network Address Translation (NAT) for traffic
leaving the protected LAN.

Private LAN addresses will be translated to the gateway's WAN address
when communicating with external networks.

Example:

    Before NAT:

    Host:       192.168.50.100
    Destination: 8.8.8.8

            │
            ▼

    Gateway WAN address: <WAN IP>

            │
            ▼

    Internet


The gateway will maintain connection state so that valid return traffic
can be translated back to the appropriate LAN client.

### NAT Security Boundary

NAT will not be treated as the primary security mechanism.

Firewall rules will determine whether traffic is permitted to cross
the LAN/WAN boundary.

NAT will provide address translation, while the firewall will provide
traffic filtering and access control.

## 4. Firewall Architecture

The gateway will use a stateful firewall to control traffic crossing
the LAN/WAN security boundary.

The firewall will use a default-deny security model for unsolicited
traffic.

### Firewall Zones

The gateway will have two primary security zones:

- **LAN:** Protected network containing trusted client devices.
- **WAN:** Untrusted upstream network.

Traffic crossing between these zones will be evaluated according to
firewall policy.

### LAN-to-WAN Traffic

Protected clients will be permitted to initiate outbound connections
according to firewall policy.

Examples of permitted traffic may include:

- TCP connections to permitted Internet services
- UDP traffic required by permitted applications
- DNS traffic to the gateway
- ICMP traffic when permitted

The gateway will track outbound connections.

Return traffic belonging to an established connection will be permitted.

### WAN-to-LAN Traffic

Unsolicited inbound traffic from the WAN will be blocked by default.

A connection originating from the WAN must not be able to directly
initiate a connection to a protected LAN client.

Example:

    WAN device
        │
        │ Connection attempt
        ▼
    Gateway
        │
        X  BLOCK
        │
        ▼
    Protected LAN

### Stateful Connection Tracking

The firewall will maintain connection state.

The gateway will distinguish between:

- New connections
- Established connections
- Related connections
- Invalid connections

Established and related traffic will be permitted when it belongs to
an allowed connection.

Invalid traffic will be rejected or dropped according to policy.

### Firewall Rules

Firewall rules may evaluate:

- Source interface
- Destination interface
- Source IP address
- Destination IP address
- Source port
- Destination port
- Transport protocol
- Connection state

The firewall will support both allow and deny rules.

### Default Security Policy

The initial security policy will follow the principle of least privilege.

By default:

- LAN clients may initiate permitted outbound traffic.
- Established return traffic is permitted.
- Unsolicited WAN-to-LAN traffic is blocked.
- Invalid traffic is blocked.
- Traffic that does not match an explicit permitted policy is denied.

### Firewall Logging

The gateway will optionally log blocked traffic.

Logged events may include:

- Timestamp
- Source address
- Destination address
- Source port
- Destination port
- Protocol
- Input interface
- Output interface
- Reason for blocking

## 5. WireGuard VPN Architecture
### VPN Design Requirements

The VPN subsystem must satisfy the following requirements:

- Protected LAN traffic must not bypass the WireGuard tunnel when VPN enforcement is enabled.
- The gateway must prevent DNS traffic from bypassing the VPN.
- The gateway must automatically attempt to restore the VPN after a connection failure.
- Normal LAN Internet access must remain blocked while the VPN is unavailable.
- WireGuard private keys must be stored securely and must not be exposed through logs or the management interface.
- VPN state must be observable through the gateway's monitoring system.
- The system must distinguish between an active, inactive, connecting, and failed VPN state.
- VPN routing and firewall enforcement must be handled by the gateway rather than relying on configuration of individual LAN clients.

## 6. DNS Architecture

The gateway will provide DNS services for protected LAN clients.

DNS traffic will be handled by the gateway rather than allowing LAN
clients to communicate directly with arbitrary external DNS servers.

### DNS Resolver

The gateway will run a local DNS forwarding service.

For the initial prototype:

- LAN clients will use the gateway as their DNS server.
- The gateway will receive DNS queries from LAN clients.
- The gateway will forward permitted queries to configured upstream
  DNS servers.
- DNS responses will be returned to the requesting LAN client.

The gateway will provide its LAN address as the DNS server:

- DNS server: `192.168.50.1`

### DNS Traffic Flow

Normal DNS resolution will follow this path:

    Host
      │
      │ DNS Query
      ▼
    Gateway
      │
      │ DNS Forwarding
      ▼
    Upstream DNS Server
      │
      ▼
    Internet

The response will follow the reverse path:

    Upstream DNS Server
      │
      ▼
    Gateway
      │
      ▼
    Host

### DNS Enforcement

The gateway will enforce DNS policy at the network boundary.

LAN clients should not be able to bypass the gateway's DNS policy by
directly communicating with external DNS servers.

The firewall may restrict direct outbound DNS traffic from LAN clients,
including:

- DNS over UDP
- DNS over TCP

Clients will instead be expected to send DNS queries to the gateway.

### VPN DNS Integration

When VPN enforcement is enabled, DNS queries must follow the VPN's
configured DNS policy.

The gateway must prevent DNS queries from being sent directly through
the WAN interface outside the VPN tunnel.

DNS traffic should therefore follow:

    Host
      │
      ▼
    Gateway DNS
      │
      ▼
    VPN Tunnel
      │
      ▼
    Configured DNS Server

If the VPN becomes unavailable, DNS access must not provide a path for
LAN clients to bypass the VPN kill switch.

### DNS Policy

The DNS subsystem will eventually support configurable policies.

Potential policies include:

- Configurable upstream DNS servers
- DNS query logging
- Domain allowlists
- Domain blocklists
- Malware-domain blocking
- Advertisement and tracking-domain blocking
- Local DNS records
- Per-client DNS policies

The initial prototype will focus on reliable DNS forwarding and
enforcement. Additional filtering capabilities will be implemented
later.

### DNS Logging and Monitoring

The gateway may record DNS activity for monitoring and troubleshooting.

Logged information may include:

- Timestamp
- Client IP address
- Requested domain
- Query type
- Response status
- Upstream DNS server
- Response time

DNS logging will be configurable so that unnecessary logging does not
consume excessive storage or system resources.

### DNS Failure Behavior

If the configured upstream DNS service becomes unavailable, the gateway
will detect the failure and attempt to use an available configured DNS
server according to its DNS policy.

When VPN enforcement is enabled, DNS failure must not cause DNS traffic
to bypass the VPN.

The gateway should expose DNS operational status through the monitoring
and management system.

## 7. DHCP Architecture

The gateway will provide Dynamic Host Configuration Protocol (DHCP)
services to devices connected to the protected LAN.

DHCP will automatically provide clients with the network configuration
required to communicate through the gateway.

### DHCP Configuration

The gateway will operate a DHCP server on the LAN interface.

The initial DHCP configuration will use:

- Network: `192.168.50.0/24`
- Gateway: `192.168.50.1`
- DHCP range: `192.168.50.100 - 192.168.50.200`
- Subnet mask: `255.255.255.0`

The gateway will provide clients with:

- IP address
- Subnet mask
- Default gateway
- DNS server

The gateway's LAN address will be provided as the client's default
gateway and DNS server.

### DHCP Traffic Flow

When a client connects to the protected LAN:

    Client
      │
      │ DHCP Discovery
      ▼
    Gateway
      │
      │ DHCP Offer
      ▼
    Client
      │
      │ DHCP Request
      ▼
    Gateway
      │
      │ DHCP Acknowledgement
      ▼
    Client configured

The client will then use the gateway for network communication.

### Default Gateway

The gateway will advertise `192.168.50.1` as the client's default
gateway.

Internet-bound traffic will therefore be sent to the security gateway
for routing and policy enforcement.

    Client
    192.168.50.100
          │
          │ Default Gateway
          ▼
    192.168.50.1
          │
          ▼
    Security Gateway

### DNS Configuration

The DHCP server will advertise `192.168.50.1` as the client's DNS
server.

This ensures that newly connected clients automatically use the
gateway's DNS service without requiring manual configuration.

### DHCP Lease Management

The gateway will maintain DHCP leases for connected clients.

The system may record:

- Client MAC address
- Assigned IP address
- Hostname
- Lease start time
- Lease expiration time

This information may later be used by the gateway's monitoring and
management system to identify connected devices.

### Static Reservations

The gateway may support DHCP reservations that associate a specific
client with a predetermined IP address.

Example:

    Client MAC Address
          │
          ▼
    192.168.50.100

This can provide consistent addressing for trusted devices while
retaining centralized DHCP management.

### DHCP Security

DHCP requests will only be accepted from the protected LAN interface.

The gateway will not provide DHCP services to the untrusted WAN.

The system will monitor for unexpected DHCP activity that could
indicate an unauthorized DHCP server or other network-security issue.

### DHCP Failure Behavior

If the gateway's DHCP service is unavailable, existing clients may
continue operating using their current leases, but new clients may be
unable to obtain network configuration.

The gateway will expose DHCP service status through the monitoring and
management system.

## 8. Network Isolation and Segmentation

The gateway will provide network segmentation and isolation controls to
limit communication between connected devices and network zones.

The purpose of network isolation is to prevent a compromised or
untrusted device from gaining unnecessary access to other protected
devices or gateway services.

### Client Isolation

The gateway may restrict direct communication between LAN clients.

For example:

    Client A
    192.168.50.100
          │
          X
          │
    Client B
    192.168.50.101

Client isolation will prevent one LAN client from directly initiating
connections to another client when the isolation policy is enabled.

This can reduce the impact of a compromised client attempting to scan,
attack, or access another connected device.

### Gateway Management Access

The gateway itself will be treated as a separate security component.

Management services such as SSH and the future web interface will only
be accessible through explicitly permitted interfaces and ports.

Management access from the WAN will be blocked by default.

The gateway will distinguish between:

- Management traffic
- Client-to-client traffic
- Client-to-Internet traffic
- Gateway-generated traffic

Each category may have separate security policies.

### Security Zones

The architecture may support multiple logical security zones in future
versions.

Potential zones include:

- **Management:** Trusted devices used to administer the gateway.
- **LAN:** General protected client devices.
- **Guest:** Untrusted client devices with Internet access but limited
  access to other local devices.
- **IoT:** Devices requiring restricted network access.
- **WAN:** Untrusted upstream network.

The initial prototype will use a single protected LAN and untrusted WAN.
Additional zones will be implemented after the basic gateway is
functional.

### Inter-Zone Traffic

Communication between security zones will be controlled by firewall
policy.

The default policy will be to deny unnecessary communication between
zones.

Permitted communication must be explicitly defined by the security
policy.

Example:

    Guest ──────► Internet       ALLOW
    Guest ──────X► LAN           BLOCK
    IoT   ──────► Internet       ALLOW
    IoT   ──────X► Management    BLOCK
    LAN   ──────► Management     POLICY
    WAN   ──────X► LAN           BLOCK

### Network Segmentation Goals

Network segmentation should:

1. Limit lateral movement between compromised devices.
2. Prevent untrusted clients from accessing management services.
3. Prevent WAN devices from directly accessing protected clients.
4. Allow controlled communication between zones when required.
5. Provide a foundation for future guest and IoT networks.

## 9. Gateway Management and Configuration

The gateway will provide a management interface for configuring,
monitoring, and maintaining the security appliance.

The management system will provide centralized control over the
gateway's networking and security functions.

### Management Interface

The initial prototype will provide command-line access for system
configuration and administration.

A web-based management interface may be implemented later to provide
a more accessible interface for configuration and monitoring.

The management system should provide access to:

- Network configuration
- Firewall configuration
- VPN configuration
- DNS configuration
- DHCP configuration
- Security policies
- System status
- Logs and monitoring data

### Configuration Management

Gateway configuration will be stored persistently on the device.

Configuration should be organized by subsystem rather than requiring
individual services to be configured independently.

Major configuration areas will include:

- Network interfaces
- LAN addressing
- DHCP
- DNS
- Firewall rules
- NAT
- WireGuard
- Security policies
- Logging
- Monitoring

The management layer will validate configuration changes before
applying them whenever possible.

### Configuration Changes

Configuration changes should follow a controlled process:

    User
      │
      ▼
    Management Interface
      │
      ▼
    Configuration Validation
      │
      ├──── Invalid ────► Reject
      │
      ▼
    Apply Configuration
      │
      ▼
    Verify System State

The gateway should avoid applying configurations that would leave the
system in an invalid or unsafe state.

### Administrative Access

Administrative access will require authentication.

Management services will be restricted to explicitly permitted
interfaces and network sources.

WAN-based administrative access will be disabled by default.

Administrative actions may be logged for auditing and troubleshooting.

### Configuration Backup

The gateway should support exporting and restoring its configuration.

Configuration backups should contain system configuration but must
protect sensitive information such as private cryptographic keys.

Backup and restore functionality will be implemented after the core
gateway functionality is operational.

### Management Availability

The management interface should remain accessible when normal Internet
connectivity is unavailable.

The gateway must therefore separate local management access from
Internet connectivity.

For example:

    Protected Host
          │
          ▼
    Gateway Management
          │
          X
       Internet

A failure of the WAN or VPN connection should not prevent local
administration of the gateway.

## 10. Monitoring and Logging

The gateway will provide monitoring and logging capabilities to provide
visibility into network activity, security events, and system health.

Monitoring will allow the administrator to determine whether the gateway
and its security controls are operating correctly.

### Network Monitoring

The gateway will monitor the state and activity of its network
interfaces.

The monitoring system may track:

- Interface state
- IP address
- Link status
- Packet counts
- Byte counts
- Connection counts
- Network errors
- Interface utilization

The system should distinguish between LAN, WAN, and VPN interface
activity.

### VPN Monitoring

The gateway will monitor the operational state of the WireGuard tunnel.

The monitoring system may record:

- VPN interface state
- Connection state
- Last successful handshake
- Tunnel uptime
- Transmitted data
- Received data
- VPN connection failures
- Reconnection attempts

VPN status should be available through the management interface.

### Firewall Monitoring

The gateway will record security-relevant firewall events.

Potential events include:

- Blocked connections
- Allowed connections
- Invalid packets
- Rejected traffic
- Connection attempts from the WAN
- Firewall configuration changes

Firewall logging should be configurable to prevent excessive log
generation.

### DNS Monitoring

The gateway may monitor DNS activity and resolver health.

Potential information includes:

- DNS queries
- Query types
- Query response status
- Upstream resolver
- Response time
- DNS failures
- Blocked domains

DNS logging should be configurable by the administrator.

### System Monitoring

The gateway will monitor its own system health.

Potential metrics include:

- CPU utilization
- Memory utilization
- Storage utilization
- System uptime
- Temperature
- Process or service status
- Network interface health

These metrics will help identify resource limitations during prototype
testing.

### Security Event Logging

Security-relevant events will be recorded separately from general
system activity when practical.

Examples include:

- Failed administrative authentication
- Firewall policy violations
- Unexpected network activity
- VPN failures
- Configuration changes
- Service failures
- Network interface changes

### Log Storage

Logs will be stored locally on the gateway.

The logging system should prevent excessive log growth from consuming
available storage.

The system may support:

- Log rotation
- Configurable retention periods
- Severity levels
- Filtering
- Exporting logs for analysis

### Monitoring and Management Integration

Monitoring data will be made available to the gateway's management
system.

The management interface should provide a high-level view of:

- Gateway status
- WAN connectivity
- LAN connectivity
- VPN status
- DNS status
- DHCP status
- Firewall activity
- System resource usage

Detailed logs should remain available for troubleshooting and security
analysis.

## 11. Security Architecture and Threat Model

The gateway is designed to protect connected host devices from threats
originating on untrusted networks.

The security architecture will follow the principles of least privilege,
defense in depth, secure defaults, and fail-closed behavior.

### Protected Assets

The primary assets protected by the gateway include:

- Host devices connected to the protected LAN
- Network traffic generated by protected clients
- DNS queries and responses
- VPN credentials and cryptographic keys
- Gateway configuration
- Gateway management services
- Security and monitoring logs

### Threat Sources

The gateway will primarily consider threats originating from:

- Untrusted Wi-Fi networks
- Other devices on the upstream network
- Malicious Internet hosts
- Compromised LAN clients
- Unauthorized users attempting to access the gateway
- Malicious or misconfigured applications
- Network-based scanning and connection attempts

### Threats

The gateway will be designed to mitigate:

- Unauthorized inbound connections
- Network scanning
- Unauthorized access to LAN clients
- Lateral movement between protected clients
- DNS bypass
- VPN traffic bypass
- IP address spoofing where practical
- Malicious or unexpected network traffic
- Unauthorized gateway administration
- Configuration tampering
- Excessive resource consumption from network traffic

The gateway cannot guarantee protection against vulnerabilities or
compromise of the protected host itself.

### Security Principles

The gateway will follow several core security principles.

#### Default Deny

Traffic will be denied unless explicitly permitted by the applicable
security policy.

#### Least Privilege

Network access will be limited to the minimum functionality required by
each client, service, and security zone.

#### Defense in Depth

Security will not depend on a single mechanism.

Multiple controls will work together, including:

- Stateful firewall
- NAT
- Network segmentation
- DNS enforcement
- VPN encryption
- Client isolation
- Authentication
- Monitoring and logging

#### Fail Closed

Security controls should fail in a manner that prevents unintended
network access.

Examples include:

- VPN failure should prevent protected traffic from bypassing the VPN.
- Invalid firewall state should not result in unrestricted forwarding.
- Unauthorized management access should be denied.
- Unsupported or unknown traffic should not automatically be trusted.

### Gateway Security

The gateway itself will be treated as a security-critical system.

The system should minimize exposed services and disable unnecessary
network services.

Administrative services will require authentication and will be
restricted to trusted interfaces or explicitly authorized sources.

Sensitive configuration data, including cryptographic private keys, will
be protected from unauthorized access.

### Threat Model Limitations

The gateway is primarily intended to defend against network-based
threats.

The initial design does not guarantee protection against:

- Physical compromise of the gateway
- Physical compromise of the protected host
- Compromise of the Linux kernel
- Compromise of trusted gateway software
- Hardware-level attacks
- Firmware-level attacks
- Attacks performed before the gateway software starts
- Malicious administrators with legitimate full access

These threats may be considered in future versions.

### Security Goals

The gateway should provide the following security properties:

1. Untrusted WAN devices cannot directly access protected LAN clients.
2. Protected LAN traffic is subject to centralized firewall policy.
3. VPN-protected traffic cannot silently bypass the VPN.
4. DNS traffic cannot silently bypass DNS enforcement.
5. Gateway management services are not exposed to the untrusted WAN by
   default.
6. Security events can be monitored and investigated.
7. Security failures should favor loss of connectivity over unintended
   network access.
8. The gateway should minimize its own attack surface.

## 12. Hardware and Performance Requirements

The gateway hardware must provide sufficient processing power, memory,
storage, and network connectivity to perform its security functions
without becoming a significant bottleneck.

The initial prototype will use a Raspberry Pi 3.

The prototype hardware is intended for development, testing, and
performance measurement rather than as the final production platform.

### Hardware Requirements

The gateway hardware should provide:

- CPU resources sufficient for routing and security processing
- Adequate memory for the operating system and gateway services
- Persistent storage for the operating system, configuration, and logs
- At least one WAN network interface
- At least one LAN network interface
- Wireless connectivity for the initial portable architecture
- Sufficient USB connectivity for external network hardware when required
- Reliable power suitable for portable operation

### Network Performance

The gateway will be evaluated based on its ability to forward traffic
while simultaneously performing security functions.

Performance measurements may include:

- Maximum routed throughput
- NAT throughput
- Firewall throughput
- VPN throughput
- DNS query performance
- Connection establishment rate
- Maximum concurrent connections
- Packet-per-second performance
- Latency introduced by the gateway

Performance should be measured with different combinations of security
features enabled.

### Resource Utilization

The system will monitor resource utilization during testing.

Measurements may include:

- CPU utilization
- Memory utilization
- Storage utilization
- CPU temperature
- Network interface utilization
- System load

Testing will determine which gateway functions create the greatest
resource requirements.

### VPN Performance

WireGuard performance will be measured separately from normal routing
performance.

Testing may compare:

- Routing without VPN
- Routing with NAT and firewall
- Routing with WireGuard
- Routing with WireGuard and full security monitoring

This will help determine the performance cost of the gateway's security
features.

### Storage Requirements

Persistent storage will be used for:

- Operating system
- Gateway configuration
- VPN configuration
- Firewall configuration
- Logs
- Monitoring data
- Management software

The system should prevent logs and monitoring data from consuming all
available storage.

### Thermal Requirements

The gateway must remain within safe operating temperatures during
sustained network activity.

Thermal performance will be evaluated during high-load testing,
particularly when VPN encryption, firewall processing, and monitoring
are enabled simultaneously.

### Power Requirements

The gateway should be capable of operating from a portable power source
when required.

Power consumption will be measured during:

- Idle operation
- Normal network activity
- High network load
- VPN operation
- Maximum sustained workload

### Prototype-to-Production Requirements

The Raspberry Pi 3 will be used to establish baseline performance and
resource requirements.

The final hardware platform will be selected based on measured
requirements rather than predetermined hardware specifications.

The upgrade process will follow:

    Prototype
       │
       ▼
    Measure
       │
       ▼
    Identify Bottlenecks
       │
       ▼
    Define Hardware Requirements
       │
       ▼
    Select Higher-Performance Platform
       │
       ▼
    Validate