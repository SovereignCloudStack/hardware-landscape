# Using OVN BGP Agent with Evpn driver in Openstack Kolla


This article covers the basics of BGP and EVPN and their applications. It focuses on the advantages of using OVN with the OVN-BGP agent compared to plain OVN.

## BGP
Border Gateway Protocol (BGP) is the protocol used to exchange routing information between different networks. It's a key component that helps the Internet function by determining the best paths for data to travel from one point to another.

## OVN BGP AGENT

The OVN BGP Agent is a component designed to integrate the Open Virtual Network (OVN) with the Border Gateway Protocol (BGP) for routing purposes. OVN is a network virtualization system that provides software-defined networking (SDN) capabilities for virtualized environments, such as OpenStack. BGP, on the other hand, is the protocol used to exchange routing information between different networks (as explained in the previous message).

### Advantages of OVN BGP vs pure OVN networking
- **Direct external network reachability / connectivity** - External access to VMs and  connectivity of VMs to external network  is simplified because the BGP agent advertises their internal IP addresses without needing NAT, Floating IP or external gateway. By using BGP, which is a standard protocol in networking, the OVN BGP Agent integrates OVN virtual networks seamlessly with existing physical routers and external network infrastructures. This allows OVN environments to be easily connected to external data centers, service provider networks, or the Internet. Without OVN BGP Agent, connecting requires configuring gateway routers or L3 devices to handle the routing between the virtual and physical networks.
- **Dynamic highly optimized routing** - The OVN BGP Agent automatically advertises the routes of the internal networks to external routers using BGP. This makes route management dynamic and automated. When a new VM or container is created, its IP is advertised without manual intervention. The BGP protocol handles the optimal route selection for traffic from external networks to reach the virtual networks. Without BGP agent, any external routing to OVN virtual networks would require static routes or manual configuration of network policies.
BGP provides intelligent path selection, allowing optimized routing of traffic between the virtual and physical networks. For example, BGP can help choose the shortest or most efficient path for traffic between the data center and external networks, potentially improving performance and reducing latency.

- **Scalability and multi-tenant environments** - The OVN BGP Agent enables scalable multi-tenant environments. Each tenant's network can be advertised separately via BGP, and policies can be applied based on BGP advertisements. This makes it easier to manage large-scale cloud environments where multiple tenants or customers need isolated but externally reachable networks. No manual configuration of floating IPs and NATs required.
- **Enhanced security** - BGP routing policies can be used to apply access controls, such as filtering routes or controlling which networks can be advertised and accepted. This allows for more granular control of how traffic flows between the virtualized environment and external networks. Without OVN BGP Agent, security policies would need to be applied manually or through static firewall and NAT configurations, which may not be as flexible or scalable as BGP-based route filtering and access control mechanisms.

The OVN BGP Agent can be used by cloud providers or large enterprises to allow external access to VMs and containers without relying on NAT.

## EVPN

Technology used for extending Layer 2 (L2) networks over Layer 3 (L3) networks,
typically in data center and WAN environments. EVPN allows multiple sites, such
as data centers or remote locations, to appear as if they are part of the same
L2 network, even though they are connected over a L3 IP network.

It is a standardized extension of BGP, more precisely of Multiprotocol BGP
(MP-BGP), which is used to advertise MAC addresses (L2) and IP prefixes (L3)
together with additional VPN information. This removes the need of flooding as
a method for MAC discovery and leads to more efficient L2 networking. Using BGP
as a single protocol for both L2 and L3 advertisements results in simplified
management with only one control plane.

Additionally, EVPN supports anycast gateways, allowing multiple routers to
provide L3 services with the same IP address, improving redundancy and
failover. It also enables seamless VM live migration across geographically
distributed environments, preserving the state of L2 and L3 connectivity.

VXLAN or MLSP are used as data plane, to deliver the L2 frames over the L3
underlay. Each tenant’s traffic is encapsulated in VXLAN tunnels between
endpoints (known as VTEPs—VXLAN Tunnel Endpoints), and BGP advertises the VXLAN
VNI (Virtual Network Identifier) mappings along with MAC/IP addresses. As an
alternative MPLS (Multi Protocol Label Switching) is well-suited for situations
where low-latency and highly predictable paths are required, or where MPLS
infrastructure already exists.

Geneve tunnels, VLANs or VXLANs can be also used by Neutron as ML2 drivers to
achieve multitenancy within the cloud itself, it is used for internal
communication between compute and network nodes. Kolla with OVN networking for
example, uses Geneve Tunnels.

When integrated with the BGP agent, the agent advertises EVPN routes (Route Type
2 for MAC/IP and Route Type 5 for IP prefixes) over the BGP protocol. OVN
logical switches and routers handle local routing and switching, and when a new
MAC or IP address is learned on a virtual network, the BGP agent advertises
this information using EVPN routes to other BGP peers. This allows the external
networks or other data centers to be aware of the internal OpenStack networks,
facilitating dynamic routing updates across sites. The BGP agent also processes
incoming EVPN routes, updating OVN’s logical network state as needed.

### Cloud interconnectivity

Leveraging existing trends towards pure L3 underlay in datacenters, using BGP
agent with EVPN allows unobtrusive interconnection of multiple cloud instances
mainly towards the goal of tenant networks federation. It eliminates the need
for complex setup of proxies and floating IPs when tenant workloads
communication is needed. It also opens scaling possibilities of deploying
multiple smaller interconnected cloud instaces instead of a single large one
providing benefits of easier day-2 lifecycle management such as independent
upgrades and more granular fault isolation. This approach enhances both the
agility and resilience of cloud environments, allowing operators to flexibly
expand or interconnect clouds in response to tenant demands without introducing
new layers of complexity.

![Cloud interconnection architecture](/documentation/assets/multi_cloud_connect.png)

### Components

#### BGPVPN API

BGP Agent uses
[networking_bgpvpn](https://github.com/openstack/networking-bgpvpn) as API for
admin to create BGPVPN objects with a Virtual Network Identifier (VNI) and BGP
Autonomous System (AS) number and provide it to tenants. Tenants can then use
it to associate BGPVPN with network or a router. BGPVPN provides a way for the
user to select which networks to expose and using different VNI also needed
tenant isolation.

#### OVN Service Plugin Driver

A simple driver which on BGPVPN association annotates VNI and AS on
Logical_Switch_Port in OVN Northbound database (NB DB) using the extra_ids
field, which then gets automatically translated into Southbound database (SB
DB) where BGP Agent can react to it.

#### OVN BGP Agent with EVPN driver

OVN BGP Agent uses a pluggable set of watchers and drivers for observing
specific changes in OVN SB DB with a watcher and run appropriate actions using
a driver. Actions mainly aim towards configuring BGP advertisements using
[FRRouting](https://frrouting.org/) and kernel routing configuration to
redirect traffic to/from OVN overlay.

![EVPN driver diagram](/documentation/assets/multi_cloud_connect.png)

EVPN driver is responsible for the networking configuration so that VMs in
exposed tenant networks are reachable through EVPN. It needs to advertise VM
IPs on the node where the traffic can be injected into OVN overlay (node where
the gateway router port is scheduled) and ensure the redirection to overlay
once the traffic reaches that node. From there the usual OVN path of a geneve
tunnel is used to reach the destination VM.

The driver uses Virtual Routing and Forwarding (VRF) to isolate the routing
for each router gateway port separately. As a transport layer to carry the
tenant traffic over the L3 underlay between the cloud instances VXLAN is used.
EVPN driver ensures the existence of a VRF device, VXLAN device, a bridge
interconnecting them and a dummy device where the IPs to be exposed are added.
For detailed list of actions taken see the
[design document](https://docs.openstack.org/ovn-bgp-agent/latest/contributor/drivers/evpn_mode_design.html)

![OVN BGP Agent with EVPN driver setup diagram](/documentation/assets/cloud-interc.png)

