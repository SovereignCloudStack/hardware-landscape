# Using OVN BGP Agent with Evpn driver in Openstack Kolla
>Note: This document is a draft

This article covers the basics of BGP and EVPN and their applications. It focuses on the advantages of using OVN with the OVN-BGP agent compared to plain OVN. Additionally, it provides a demo setup of the OVN-BGP agent with EVPN in Kolla Ansible.

## BGP
Border Gateway Protocol (BGP) is the protocol used to exchange routing information between different networks. It's a key component that helps the Internet function by determining the best paths for data to travel from one point to another.

## OVN BGP AGENT

The OVN BGP Agent is a component designed to integrate the Open Virtual Network (OVN) with the Border Gateway Protocol (BGP) for routing purposes. OVN is a network virtualization system that provides software-defined networking (SDN) capabilities for virtualized environments, such as OpenStack. BGP, on the other hand, is the protocol used to exchange routing information between different networks (as explained in the previous message).

### Advantages of OVN BGP vs pure OVN networking
- **Direct External Network Reachability / connectivity** - External access to VMs and  connectivity of VMs to external network  is simplified because the BGP agent advertises their internal IP addresses without needing NAT, Floating IP or external gateway.
- **Dynamic highly optimized routing** - he OVN BGP Agent automatically advertises the routes of the internal networks to external routers using BGP. This makes route management dynamic and automated. When a new VM or container is created, its IP is advertised without manual intervention. The BGP protocol handles the optimal route selection for traffic from external networks to reach the virtual networks. Without BGP agent, any external routing to OVN virtual networks would require static routes or manual configuration of network policies.
BGP provides intelligent path selection, allowing optimized routing of traffic between the virtual and physical networks. For example, BGP can help choose the shortest or most efficient path for traffic between the data center and external networks, potentially improving performance and reducing latency.

- **Seamless Integration with Physical Networks** - By using BGP, which is a standard protocol in networking, the OVN BGP Agent integrates OVN virtual networks seamlessly with existing physical routers and external network infrastructures. This allows OVN environments to be easily connected to external data centers, service provider networks, or the Internet. Without OVN BGP Agent, connecting requires configuring gateway routers or L3 devices to handle the routing between the virtual and physical networks.
- **Scalability and Multi-Tenant Environments** - The OVN BGP Agent enables scalable multi-tenant environments. Each tenant's network can be advertised separately via BGP, and policies can be applied based on BGP advertisements. This makes it easier to manage large-scale cloud environments where multiple tenants or customers need isolated but externally reachable networks. No manual configuration of floating IPs and NATs required.
- **Enhanced Security** - BGP routing policies can be used to apply access controls, such as filtering routes or controlling which networks can be advertised and accepted. This allows for more granular control of how traffic flows between the virtualized environment and external networks. Without OVN BGP Agent, security policies would need to be applied manually or through static firewall and NAT configurations, which may not be as flexible or scalable as BGP-based route filtering and access control mechanisms.

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

When integrated with the BGP agent, the agent advertises EVPN routes (Route Type
2 for MAC/IP and Route Type 5 for IP prefixes) over the BGP protocol. OVN
logical switches and routers handle local routing and switching, and when a new
MAC or IP address is learned on a virtual network, the BGP agent advertises
this information using EVPN routes to other BGP peers. This allows the external
networks or other data centers to be aware of the internal OpenStack networks,
facilitating dynamic routing updates across sites. The BGP agent also processes
incoming EVPN routes, updating OVN’s logical network state as needed.


### EVPN driver for OVN BGP Agent

![Alt text](/documentation/assets/cloud-interc.png)


#### BGPVPN API

user calls this api and it creates bgpvpn/network/router/port in neutron DB

#### BGPVPN OVN Driver
propagates resources created by api to OVN NB DB
Problem: the standard driver (bagpipe) is for ML2/OVS networks. So it does not propagate to OVN NB DB by default.
#### OVN NB DB
The NB database serves as the interface for users and applications to configure the network. It contains high-level network information and is designed for user interaction.

#### OVN SB DB

The SB database is responsible for the actual implementation of the network state. It reflects the current state of the network as observed by the OVN components, such as the OVN controllers and data planes.

#### OVN BGP Agent EVPN Driver
watches SB DB and creates appropriate rounting when `chassisredirect` type of `Port_Binding` is created in SB DB, it calls `expose_ip` method that. Creates all the VRF/VXLAN configuration (devices and its connection to the OVN overlay) as well as the VRF configuration at FRR.

### OVN BGP Agent in Kolla-Ansible
This part is a quick how-to for setting up OVN BGP Agent in Kolla-ansible.
There's an existing [PR](https://review.opendev.org/c/openstack/kolla-ansible/+/891622) in kolla-ansible upstream, however it does not work properly. I created a [PR in kolla-ansible fork](https://github.com/SovereignCloudStack/kolla-ansible/pull/5) as well as in [kolla fork](https://github.com/SovereignCloudStack/kolla/pull/2) that attempts to fix the issues.

I got all containers running, however they do not seem to activate  (see below)
#### Steps
- Get a working test environment i.e. testbed, cloud-in-a-box, [kolla-builder](https://github.com/SovereignCloudStack/kolla-builder)
> Note: if you use kolla-builder you need to checkout [this branch](https://github.com/SovereignCloudStack/kolla-builder/tree/ovn-bgp-agent-inventory) to update inventory
- Clone  [kola fork](https://github.com/SovereignCloudStack/kolla)
```
git clone git@github.com:SovereignCloudStack/kolla.git
```
>Note: the  steps regarding building kolla images are recommended the all-in-one VM spawned by kolla-builder rather than your local machine to simplyfy deployment.
>- run `./pre-deploy` script on the VM (this will install docker)
>- repeat steps ommitting pushing images as it is not necessary, them being already there

to simplyfy
- Checkout `ovn-bgp-agent` branch in both kolla
```>Note: as said above, skip this step if you built your images on kolla-builder all-in-one VM
cd kolla
git checkout ovn-bgp-agent
```
- Install kolla (edit mode is recommended)
```
# in kolla directory
pip install -e .
```
- Build images
```
kolla-build ovn-bgp-agent frr neutron horizon
```
- Get images tag
```
dokcer image ls
# EXAMPLE OUTPUT
REPOSITORY                                          TAG              IMAGE ID       CREATED        SIZE
kolla/neutron-mlnx-agent                            17.1.0           862918488114   11 days ago    1.58GB
kolla/neutron-l3-agent                              17.1.0           e908f72c8a66   11 days ago    1.56GB
kolla/neutron-linuxbridge-agent                     17.1.0           2368a2de4cba   11 days ago    1.53GB
kolla/neutron-infoblox-ipam-agent                   17.1.0           1a91373e9e5a   11 days ago    1.54GB
kolla/neutron-server                                17.1.0           52f069a2025a   11 days ago    1.54GB
kolla/neutron-bgp-dragent                           17.1.0           9a52fcab6090   11 days ago    1.53GB
kolla/neutron-sriov-agent                           17.1.0           d10be7b0502f   11 days ago    1.53GB
kolla/neutron-openvswitch-agent                     17.1.0           7612f83e42e0   11 days ago    1.53GB
kolla/neutron-dhcp-agent                            17.1.0           ada8ead6a695   11 days ago    1.53GB
kolla/neutron-metering-agent                        17.1.0           887841baf635   11 days ago    1.53GB
kolla/neutron-metadata-agent                        17.1.0           f9f6e4188dbd   11 days ago    1.53GB
kolla/neutron-ovn-agent                             17.1.0           c69e3b9a0ecc   11 days ago    1.53GB
kolla/ironic-neutron-agent                          17.1.0           7c7d9e0f4cac   11 days ago    1.53GB
kolla/neutron-base                                  17.1.0           0bb7236a857f   11 days ago    1.53GB
kolla/openstack-base                                17.1.0           a498ab05494c   11 days ago    1.17GB
kolla/horizon                                       17.1.0           c694f5bda748   12 days ago    1.4GB
kolla/ovn-bgp-agent                                 17.1.0           822880a9ec91   12 days ago    1.58GB
kolla/frr                                           17.1.0           8b6a4226d03e   12 days ago    672MB
kolla/base                                          17.1.0           cbdec5ad8b29   12 days ago    631MB
```

- Push images
```
# Example commands
docker image tag kolla/neutron-server:17.1.0  registry-host:5000/myadmin/kolla/neutron-server:latest
docker image push registry-host:5000/myadmin/kolla/neutron-server:latest
# Do this for every image that was built
```
>Note: as said above, skip this step if you built your images on kolla-builder all-in-one VM

- With your images ready you can clone [kolla ansible fork](https://github.com/SovereignCloudStack/kolla-ansible)
```
git clone git@github.com:SovereignCloudStack/kolla-ansible.git
```
- Checkout `ovn-bgp-agent` for kolla-ansible fork
```
cd kolla-ansible
git checkout ovn-bgp-agent
```
- Here are example variables you can add to your `globals.yaml` for `ovn-bgp-agent`
```yaml
# Use only with kolla-builder if you built your images on the VM
frr_image_full: "kolla/frr:17.1.0"
ovn_bgp_agent_image_full: "kolla/ovn-bgp-agent:17.1.0"
horizon_image_full: "kolla/horizon:17.1.0"
neutron_server_image_full: "kolla/neutron-server:17.1.0"
neutron_metadata_agent_image_full: "kolla/neutron-metadata-agent:17.1.0"
####

enable_ovn_bgp_agent: "yes"
ovn_bgp_agent_driver: "ovn_evpn_driver"
ovn_bgp_agent_exposing_method: "vrf"
neutron_plugin_agent: ovn


bgp_local_asn: "64999"
# This has to be a loopback ip of `br-ex` interface
bgp_loopback_ip: "1.1.1.1"
bgp_loopback_interface: "br-ex"

enable_neutron_bgpvpn: "yes"
```
