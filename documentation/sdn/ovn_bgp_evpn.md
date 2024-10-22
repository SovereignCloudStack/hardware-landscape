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

## Test deployment of OVN BGP Agent in Kolla-Ansible
This part is a quick how-to for setting up OVN BGP Agent in Kolla-ansible.
There's an existing [PR](https://review.opendev.org/c/openstack/kolla-ansible/+/891622) in kolla-ansible upstream, however it does not work properly. I created a [PR in kolla-ansible fork](https://github.com/SovereignCloudStack/kolla-ansible/pull/5) as well as in [kolla fork](https://github.com/SovereignCloudStack/kolla/pull/2) that attempts to fix the issues.

I got all containers running, however they do not seem to activate  (see below)
### Steps
- Get a working test environment i.e. testbed, cloud-in-a-box, [kolla-builder](https://github.com/SovereignCloudStack/kolla-builder)

 - If you use kolla-builder, you need to checkout a dev branch `ovn-bgp-agent-deployment`
 ```bash
 git fetch origin ovn-bgp-agent-deployment:ovn-bgp-agent-deployment
 git checkout ovn-bgp-agent-deployment
 ```
 - Use the following variable file with kolla-builder
```yaml
inventory_name: "ovn-bgp"
image_pool: "/home/matus/pool"
image_path: "{{ image_pool }}/kolla-image.qcow2"
ara_enable: false
is_remote: false
python_bin_path: "/home/matus/scs/kolla-venv/bin"
# Use different CIDRs and virbrX interfaces if
# the provided ones are already in use
network_ssh: "kolla-ssh-bgp-flat"
network_openstack: "kolla-openstack-bgp-flat"
network_neutron: "kolla-neutron-bgp-flat"
network_ssh_ip: "192.168.122.1"
network_openstack_ip: "192.168.123.0"
network_neutron_ip: "192.168.100.0"
network_ssh_bridge: virbr0
network_openstack_bridge: virbr1
network_neutron_bridge: virbr2
create_networks: true
kolla_internal_vip_address: "192.168.123.200"
git_patch_kolla: true
git_branch: "ovn-bgp-agent"
git_patches: []
kolla_ssh_key: "{{ lookup('ansible.builtin.env', 'HOME') }}/.ssh/id_kolla"
ssh_config: "ssh_config"
globals_file: user-globals/ovn-bgp.yml
kolla_source_local_path: "<path to kolla ansible source code>"
is_aio: true
node_name: "kolla-ovn-bgp-flat"
ram_size: 10000
cpu_count: 12

```
- Clone  [kola fork](https://github.com/SovereignCloudStack/kolla)
```
git clone git@github.com:SovereignCloudStack/kolla.git
```
>Note: the  steps regarding building kolla images are recommended the all-in-one VM spawned by kolla-builder rather than your local machine to simplyfy deployment.
>- run `./pre-deploy` script on the VM (this will install docker)
>- repeat steps ommitting pushing images as it is not necessary, them being already there

to simplyfy
- Checkout `ovn-bgp-agent` branch in  kolla
```>Note: as said above, skip this step if you built your images on kolla-builder all-in-one VM
cd kolla
git fetch origin ovn-bgp-agent:ovn-bgp-agent
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
git fetch origin ovn-bgp-agent:ovn-bgp-agent
git checkout ovn-bgp-agent
```
- If you used kolla builder with locally built images add this to your `globals.yaml`
```yaml
# Use only with kolla-builder if you built your images on the VM
docker_tag: "0.1.0" # Replace with your images tag
frr_image_full: "kolla/frr:{{ docker_tag }}"
ovn_bgp_agent_image_full: "kolla/ovn-bgp-agent:{{ docker_tag }}"
horizon_image_full: "kolla/horizon:{{ docker_tag }}"
neutron_server_image_full: "kolla/neutron-server:{{ docker_tag }}"
neutron_metadata_agent_image_full: "kolla/neutron-metadata-agent:{{ docker_tag }}"
####
```

- It is also recommended,however not necessary, to clone ovn-bgp-agent and mount it to containers. This way it is easier
to debug the agent. If you use kolla builder you can do this by adding the following to your variables file. If you use other environment, make sure the source code path is accessible by ovn-bgp-agent container
```yaml
additional_uploads_deploy_node:
- "<path to ovn bgp agent source>"
additional_upload_node_path: "/home/kolla"
# This is important for
additional_upload_mode: "0777"
```
- Then mount the source code by adding this to `globals.yml`
```yaml
default_extra_volumes:
- "/home/kolla/ovn-bgp-agent/ovn_bgp_agent:/var/lib/kolla/venv/lib/python3.9/site-packages/ovn_bgp_agent"
```
## Example deployments
### NB/SB Driver BGP advertising
#### Steps
- Spawn a test VM with `frr` installed `sudo apt install frr` configure bgp peering
```
frr version 9.1.2
frr defaults traditional
hostname <your VM hostname>
log file /var/log/frr/frr.log
!
router bgp 65001
 bgp router-id 1.1.1.0
 bgp log-neighbor-changes
 no bgp ebgp-requires-policy
 no bgp default ipv4-unicast
 bgp graceful-shutdown
 neighbor kolla peer-group
 neighbor kolla remote-as 65001
 neighbor kolla remote-as internal
 neighbor <INTERFACE THAT IS ON THE SAME NETWORK AS KOLLA> interface peer-group kolla
 neighbor <IP ADRESS OF KOLLA AIO VM> peer-group kolla
 !
 address-family ipv4 unicast
  neighbor kolla activate
 exit-address-family
 !
 address-family ipv6 unicast
  neighbor kolla activate
 exit-address-family
exit
```
- Deploy kolla-ansible **without** OVN BGP agent on. This will create necessary to create ovs bridges.
- For this we are going to use `underlay` exposing method, which requires `br-ex` interface to be up.
```bash
sudo ip l set br-ex up
```
- Add a loopback ip to the `br-ex` interface
```bash
sudo ip a add 1.1.1.1/32 dev br-ex
```
- Add the following to your `globals.yaml`
```yaml
enable_ovn_bgp_agent: "yes"

ovn_bgp_agent_driver: "ovn_bgp_driver"
# for nb driver
# ovn_bgp_agent_driver: "nb_ovn_bgp_driver"
# NOTE: currently didn't manage to run nb_driver in my test environment
ovn_bgp_agent_exposing_method: "underlay"
neutron_plugin_agent: "ovn"
bgp_expose_tenant_networks: "yes"
bgp_local_asn: "64999"
bgp_loopback_ip: "172.30.1.1"
# Ip of a machine you want to advertise bgp routes to
frr_neighbor_ip: "<IP ADRESS OF TEST VM>"
```
- Deploy kolla-ansible again, with new globals.
```bash
kolla-ansible -i all-in-one deploy --tags ovn-bgp-agent,frr
```
- New interfaces will be added  `bgp-vrf` and `bgp-nic`
- Adding new floating IPs, rounters or VMs to provider network will expose them by adding them to `bgp-nic`
```bash
ip a show bgp-nic
# Example output
9: bgp-nic: <BROADCAST,NOARP,UP,LOWER_UP> mtu 1500 qdisc noqueue master bgp-vrf state UNKNOWN group default qlen 1000
    link/ether 16:23:48:49:bb:a6 brd ff:ff:ff:ff:ff:ff
    inet 192.168.100.186/32 scope global bgp-nic
       valid_lft forever preferred_lft forever
    inet 192.168.100.194/32 scope global bgp-nic
       valid_lft forever preferred_lft forever
    inet 192.168.100.187/32 scope global bgp-nic
       valid_lft forever preferred_lft forever
```

### Notes/TODO

- There seems to be an error in ovn-bgp-agent, it's described in this [launchpad](https://lists.launchpad.net/yahoo-eng-team/msg94358.html)

    - This error can be avoided but it requires some hacking
    - it seems that the externam MAC is in `external_ids` field
    ```python
    allowed_ext_ips = [],
    exempted_ext_ips = [],
    external_ids = {
        'neutron:fip_external_mac': 'fa:16:3e:36:86:20',
        'neutron:fip_id': '3a329994-10bf-4631-bb0f-7ad5a71a93f9',
        'neutron:fip_network_id': 'b0d4aec5-6a4b-45fc-a530-f7c048cfc4ae',
        'neutron:fip_port_id': '9daa4dac-f9ec-44a5-b8e1-6455fca554ac',
        'neutron:revision_number': '2',
        'neutron:router_name': 'neutron-ef88cdb6-500e-46ac-afbc-6f04d5d25656'
    },
    external_ip = 192.168.100.182,
    external_mac = [],
    external_port_range = '',
    gateway_port = [<ovs.db.idl.Row object at 0x7f3c0647a0d0>],
    logical_ip = 10.0.0.62,
    logical_port = ['9daa4dac-f9ec-44a5-b8e1-6455fca554ac'],
    options = {},
    type = dnat_and_snat
    ```
    - Maybe it's some wrong setting in neutron
    - Anyway, a patch like this can be made
    ```python
        def get_port_external_ip_and_ls(self, port):
        nat_entry = self.nb_idl.get_nat_by_logical_port(port)
        if not nat_entry:
            return None, None, None
        net_id = nat_entry.external_ids.get(constants.OVN_FIP_NET_EXT_ID_KEY)
        # Add a try block
        try:
            mac = nat_entry.external_mac[0]
        except IndexError:
            mac = nat_entry.external_ids['neutron:fip_external_mac']
        if not net_id:
            return nat_entry.external_ip,mac, None
        else:
            ls_name = "neutron-{}".format(net_id)
            return nat_entry.external_ip, mac , ls_name
    ```
- Underlay exposed ips are not reachable (cannot ssh into instances) when using nb_driver. It might be due to wrong OVN configuration reffer to this note
>NOTE:
As we also want to be able to expose VM connected to tenant networks (when expose_tenant_networks or `expose_ipv6_gua_tenant_networks` configuration options are enabled), there is a need to expose the Neutron router gateway port (cr-lrp on OVN) so that the traffic to VMs in tenant networks is injected into OVN overlay through the node that is hosting that port.
