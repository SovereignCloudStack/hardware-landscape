# The networking setup

# General

Für the setup of the SCS Hardware Landscape, instead of a classic Layer2 underlay, we have set up a
Layer3 underlay based on the design [developed by the team](https://scs.community/de/2024/02/09/sdn-scalability/) and more commonly
used in larger cloud platforms.

Instead of maintaining a common Layer2 broadcast domain between the nodes or partitioning different function groups
into broadcast domains, we chose an approach that is suitable for larger platforms or that also makes sense for new platforms
to be set up, as subsequent adaptation can be very time-consuming.

With the chosen ‘Layer3-Underlay-BGP-to-the-Host’, the eBGP protocol is used to efficiently (especially for larger environments)
organise the the path-descision of packets between nodes.

Unlike a classic layer 2 network, this provides the following advantages:

- No Spanning-Tree complexities, no constant churn in MAC tables
- No more Multichassis-LACP interoperability and design topics
- A scalable setup for larger or critical environments with a high number of nodes
  (layer 2 is simpler and more efficient; with a high number of nodes, layer 3 underlays cause a number of complex problems that layer 2 does not)
- Connections can be transported and routed with fewer problems and dynamically over different network paths depending on preference and the availability of the same
- The use of ECMP ensures that the number of communication relationships to a specific destination
  is evenly distributed over competing paths (regardless of the amount of data these communication relationships exchange).
  (an approximate load distribution)
- BGP/Anycast allows the IP addresses of services to be made concurrently available at several locations
- Support for fast convergence of routing state across the network
- Support for draining traffic from a node to be taken down
- Support for filtering inbound and outbound advertisement
[//]: <> TODO: Clarify/rework
[//]: <> - Tenant traffic is encapsulated in Geneve or VXLAN in the packets transported using the layer3 underlay
[//]: <>  (the configuration of the network switches can be kept very simple and there is no limitation to 4096 tenant networks like in layer2/VLAN)
- BGP IPv6 unnumbered simplifies the ip-adressing scheme design requirements of layer3 networks significantly
- Future: Support for establishing EVPN (tenant) connections using the Multiprotocol BGP Support (see RFC 4760)

As a consequence, this means that BGP routers with private ASN numbers are active on all systems involved
(e.g. servers and switches) in the cloud setup and these exchange information with each other via the network topology.

As a result, redundant paths of a server system, for example, are no longer managed via (multi-chassis) LACP,
but the respective server or switch has topology information that allows it to route traffic efficiently or deal with availability problems.

The detailes of this concept are heavily releated to the [great network documentation](https://docs.metal-stack.io/stable/overview/networking/) of
(see also the [Github PR](https://github.com/metal-stack/docs/pull/209/files), or the [extended networking document](https://github.com/scoopex/metal-stack-docs/blob/master/docs/src/overview/networking.md) Metal-Stack.
Furthermore, the present design is strongly inspired by the work of Dinesh G. Dutt on BGP ([bgp-ebook](https://www.nvidia.com/en-us/networking/border-gateway-protocol/)) and the
work ‘[Cloud Native Data Centre Networking](https://www.oreilly.com/library/view/cloud-native-data/9781492045595/)’ (O'Reilly)
published in 2019, which provides various interesting basics.
Openstack also provides a interesting "[Networking concepts](https://docs.openstack.org/arch-design/design-networking/design-networking-concepts.html)"
document which provides various details related to layer3 underlays.

# The networking diagram

This diagram visualizes the physical (devices, and wiring) and logical (VLANs, Routed, BGP/ASN) setup of the environment.

![The network connections/associations](assets/Network_Setup.drawio.svg)

**Hints**

* Edit with https://app.diagrams.net/
* Save as SVG image with embedded draw.io data

# Node Networking Setup

The following section provides an insight into what the ‘Layer3-Underlay-BGP-to-the-Host’ setup looks like on the cloud
nodes through the output of various network commands and files.


## The configurations Files

### The Interface configuration

```bash
root@st01-stor-r01-u01:/home/scoopex# cat /etc/netplan/01-osism.yaml
# This file describes the network interfaces available on your system
# For more information, see netplan(5).
---
network:
  version: 2
  renderer: networkd

  bonds:
    {}


  bridges:
    {}



  ethernets:
    dummy0:
        addresses:
        - 10.10.21.21/32
        - fd0c:cc24:75a0:1:10:10:21:21/128
    enp66s0f0np0:
        dhcp4: 'no'
        dhcp6: 'no'
        mtu: 9100
    enp66s0f1np1:
        dhcp4: 'no'
        dhcp6: 'no'
        mtu: 9100


  tunnels:
    {}


  vlans:
    {}


  vrfs:
    {}
```

### The configuration of the FRRouting Daemon

```bash
root@st01-stor-r01-u01:/home/scoopex# cat /etc/frr/frr.conf
frr version 8.1
frr defaults traditional
hostname st01-stor-r01-u01
log syslog informational
service integrated-vtysh-config
!
router bgp 4210021021
 no bgp ebgp-requires-policy
 bgp bestpath as-path multipath-relax
 bgp router-id 10.10.21.21
 neighbor enp66s0f0np0 interface remote-as 65405
 neighbor enp66s0f1np1 interface remote-as 65404
 !
 address-family ipv4 unicast
  redistribute connected route-map bgp_out
  neighbor enp66s0f0np0 route-map bgp_out out
  neighbor enp66s0f1np1 route-map bgp_out out
  maximum-paths 2
 exit-address-family
 !
 address-family ipv6 unicast
  redistribute connected route-map bgp_out
  neighbor enp66s0f0np0 activate
  neighbor enp66s0f0np0 route-map bgp_out out
  neighbor enp66s0f1np1 activate
  neighbor enp66s0f1np1 route-map bgp_out out
 exit-address-family
exit
!
route-map bgp_out permit 10
 match interface dummy0
exit
!
route-map RM_SET_SRC4 permit 10
 set src 10.10.21.21
exit
!
route-map RM_SET_SRC6 permit 10
 set src fd0c:cc24:75a0:1:10:10:21:21
exit
!
ip protocol bgp route-map RM_SET_SRC4
!
ipv6 protocol bgp route-map RM_SET_SRC6

```

## Output of the disagnostic tools


### Interfaces

```bash
# ip link ls
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
2: enp66s0f0np0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc mq state UP mode DEFAULT group default qlen 1000
    link/ether 14:23:f2:cb:86:e0 brd ff:ff:ff:ff:ff:ff
3: enp66s0f1np1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc mq state UP mode DEFAULT group default qlen 1000
    link/ether 14:23:f2:cb:86:e1 brd ff:ff:ff:ff:ff:ff
....
7: dummy0: <BROADCAST,NOARP,UP,LOWER_UP> mtu 9000 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/ether ee:33:e4:bc:b8:5b brd ff:ff:ff:ff:ff:ff
...

root@st01-stor-r01-u01:/home/scoopex# ip addr ls

1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: enp66s0f0np0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc mq state UP group default qlen 1000
    link/ether 14:23:f2:cb:86:e0 brd ff:ff:ff:ff:ff:ff
    inet6 fe80::1623:f2ff:fecb:86e0/64 scope link
       valid_lft forever preferred_lft forever
3: enp66s0f1np1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc mq state UP group default qlen 1000
    link/ether 14:23:f2:cb:86:e1 brd ff:ff:ff:ff:ff:ff
    inet6 fe80::1623:f2ff:fecb:86e1/64 scope link
       valid_lft forever preferred_lft forever
...
7: dummy0: <BROADCAST,NOARP,UP,LOWER_UP> mtu 9000 qdisc noqueue state UNKNOWN group default qlen 1000
    link/ether ee:33:e4:bc:b8:5b brd ff:ff:ff:ff:ff:ff
    inet 10.10.21.21/32 scope global dummy0
       valid_lft forever preferred_lft forever
    inet6 fd0c:cc24:75a0:1:10:10:21:21/128 scope global
       valid_lft forever preferred_lft forever
    inet6 fe80::ec33:e4ff:febc:b85b/64 scope link
       valid_lft forever preferred_lft forever
...
```

### Routing

**FRRouting status**

```bash
root@st01-stor-r01-u01:/home/scoopex# vtysh

Hello, this is FRRouting (version 8.1).
Copyright 1996-2005 Kunihiro Ishiguro, et al.

st01-stor-r01-u01# show ip bgp summary

IPv4 Unicast Summary (VRF default):
BGP router identifier 10.10.21.21, local AS number 4210021021 vrf-id 0
BGP table version 26
RIB entries 41, using 7544 bytes of memory
Peers 2, using 1446 KiB of memory

Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
enp66s0f0np0    4      65405      1311      1268        0    0    0 21:02:40           20        1 N/A
enp66s0f1np1    4      65404      1309      1268        0    0    0 21:02:40           20        1 N/A

Total number of neighbors 2

st01-stor-r01-u01# show ip route
Codes: K - kernel route, C - connected, S - static, R - RIP,
       O - OSPF, I - IS-IS, B - BGP, E - EIGRP, N - NHRP,
       T - Table, v - VNC, V - VNC-Direct, A - Babel, F - PBR,
       f - OpenFabric,
       > - selected route, * - FIB route, q - queued, r - rejected, b - backup
       t - trapped, o - offload failure

B>* 10.10.21.4/32 [20/0] via fe80::d277:ceff:fe4b:b47a, enp66s0f1np1, weight 1, 21:07:12
B>* 10.10.21.5/32 [20/0] via fe80::d277:ceff:fec1:6380, enp66s0f0np0, weight 1, 21:07:12
B>* 10.10.21.6/32 [20/0] via fe80::d277:ceff:fe4b:b47a, enp66s0f1np1, weight 1, 21:07:12
  *                      via fe80::d277:ceff:fec1:6380, enp66s0f0np0, weight 1, 21:07:12
B>* 10.10.21.7/32 [20/0] via fe80::d277:ceff:fe4b:b47a, enp66s0f1np1, weight 1, 21:07:12
  *                      via fe80::d277:ceff:fec1:6380, enp66s0f0np0, weight 1, 21:07:12
B>* 10.10.21.10/32 [20/0] via fe80::d277:ceff:fe4b:b47a, enp66s0f1np1, weight 1, 21:07:12
  *                       via fe80::d277:ceff:fec1:6380, enp66s0f0np0, weight 1, 21:07:12
B>* 10.10.21.11/32 [20/0] via fe80::d277:ceff:fe4b:b47a, enp66s0f1np1, weight 1, 21:07:12
  *                       via fe80::d277:ceff:fec1:6380, enp66s0f0np0, weight 1, 21:07:12
B>* 10.10.21.12/32 [20/0] via fe80::d277:ceff:fe4b:b47a, enp66s0f1np1, weight 1, 19:09:17
  *                       via fe80::d277:ceff:fec1:6380, enp66s0f0np0, weight 1, 19:09:17
B>* 10.10.21.13/32 [20/0] via fe80::d277:ceff:fe4b:b47a, enp66s0f1np1, weight 1, 21:07:12
  *                       via fe80::d277:ceff:fec1:6380, enp66s0f0np0, weight 1, 21:07:12
B>* 10.10.21.14/32 [20/0] via fe80::d277:ceff:fe4b:b47a, enp66s0f1np1, weight 1, 21:07:12
  *                       via fe80::d277:ceff:fec1:6380, enp66s0f0np0, weight 1, 21:07:12
C>* 10.10.21.21/32 is directly connected, dummy0, 21:07:15
B>* 10.10.21.22/32 [20/0] via fe80::d277:ceff:fe4b:b47a, enp66s0f1np1, weight 1, 21:07:12
  *                       via fe80::d277:ceff:fec1:6380, enp66s0f0np0, weight 1, 21:07:12
B>* 10.10.21.23/32 [20/0] via fe80::d277:ceff:fe4b:b47a, enp66s0f1np1, weight 1, 21:07:12
  *                       via fe80::d277:ceff:fec1:6380, enp66s0f0np0, weight 1, 21:07:12
B>* 10.10.21.24/32 [20/0] via fe80::d277:ceff:fe4b:b47a, enp66s0f1np1, weight 1, 21:07:12
  *                       via fe80::d277:ceff:fec1:6380, enp66s0f0np0, weight 1, 21:07:12
B>* 10.10.21.25/32 [20/0] via fe80::d277:ceff:fe4b:b47a, enp66s0f1np1, weight 1, 21:07:12
  *                       via fe80::d277:ceff:fec1:6380, enp66s0f0np0, weight 1, 21:07:12
B>* 10.10.21.26/32 [20/0] via fe80::d277:ceff:fe4b:b47a, enp66s0f1np1, weight 1, 21:07:12
  *                       via fe80::d277:ceff:fec1:6380, enp66s0f0np0, weight 1, 21:07:12
B>* 10.10.21.27/32 [20/0] via fe80::d277:ceff:fe4b:b47a, enp66s0f1np1, weight 1, 21:07:12
  *                       via fe80::d277:ceff:fec1:6380, enp66s0f0np0, weight 1, 21:07:12
B>* 10.10.21.28/32 [20/0] via fe80::d277:ceff:fe4b:b47a, enp66s0f1np1, weight 1, 21:07:12
  *                       via fe80::d277:ceff:fec1:6380, enp66s0f0np0, weight 1, 21:07:12
B>* 10.10.21.29/32 [20/0] via fe80::d277:ceff:fe4b:b47a, enp66s0f1np1, weight 1, 21:07:12
  *                       via fe80::d277:ceff:fec1:6380, enp66s0f0np0, weight 1, 21:07:12
B>* 10.10.21.30/32 [20/0] via fe80::d277:ceff:fe4b:b47a, enp66s0f1np1, weight 1, 21:07:12
  *                       via fe80::d277:ceff:fec1:6380, enp66s0f0np0, weight 1, 21:07:12
B>* 10.10.21.200/32 [20/0] via fe80::d277:ceff:fe4b:b47a, enp66s0f1np1, weight 1, 19:12:55
  *                        via fe80::d277:ceff:fec1:6380, enp66s0f0np0, weight 1, 19:12:55
B>* 10.10.21.201/32 [20/0] via fe80::d277:ceff:fe4b:b47a, enp66s0f1np1, weight 1, 19:12:55
  *                        via fe80::d277:ceff:fec1:6380, enp66s0f0np0, weight 1, 19:12:55
C>* 172.31.101.160/28 is directly connected, br-d3eef6ce6b47, 21:07:01


st01-stor-r01-u01# show ip bgp neighbors
BGP neighbor on enp66s0f0np0: fe80::d277:ceff:fec1:6380, remote AS 65405, local AS 4210021021, external link
Hostname: st01-sw25g-r01-u35
  BGP version 4, remote router ID 10.10.21.5, local router ID 10.10.21.21
  BGP state = Established, up for 21:04:18
  Last read 00:00:18, Last write 00:00:18
  Hold time is 180, keepalive interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv4 Unicast: RX advertised and received
      IPv6 Unicast: RX advertised and received
    Extended nexthop: advertised and received
      Address families by peer:
                   IPv4 Unicast
    Route refresh: advertised and received(old & new)
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: advertised and received
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: st01-stor-r01-u01,domain name: n/a) received (name: st01-sw25g-r01-u35,domain name: n/a)
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv4 Unicast, IPv6 Unicast
    End-of-RIB received: IPv4 Unicast, IPv6 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: False
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
    IPv4 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                  1          1
    Notifications:          0          0
    Updates:                4         47
    Keepalives:          1265       1265
    Route Refresh:          0          0
    Capability:             0          0
    Total:               1270       1313
  Minimum time between advertisement runs is 0 seconds

 For address family: IPv4 Unicast
  Update group 1, subgroup 1
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  Outbound path policy configured
  Route map for outgoing advertisements is *bgp_out
  20 accepted prefixes

 For address family: IPv6 Unicast
  Update group 2, subgroup 2
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  Outbound path policy configured
  Route map for outgoing advertisements is *bgp_out
  18 accepted prefixes

  Connections established 1; dropped 0
  Last reset 21:04:19,  Waiting for peer OPEN
Local host: fe80::1623:f2ff:fecb:86e0, Local port: 49256
Foreign host: fe80::d277:ceff:fec1:6380, Foreign port: 179
Nexthop: 10.10.21.21
Nexthop global: fe80::1623:f2ff:fecb:86e0
Nexthop local: fe80::1623:f2ff:fecb:86e0
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 120
Read thread: on  Write thread: on  FD used: 24

BGP neighbor on enp66s0f1np1: fe80::d277:ceff:fe4b:b47a, remote AS 65404, local AS 4210021021, external link
Hostname: st01-sw25g-r01-u34
  BGP version 4, remote router ID 10.10.21.4, local router ID 10.10.21.21
  BGP state = Established, up for 21:04:18
  Last read 00:00:18, Last write 00:00:18
  Hold time is 180, keepalive interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv4 Unicast: RX advertised and received
      IPv6 Unicast: RX advertised and received
    Extended nexthop: advertised and received
      Address families by peer:
                   IPv4 Unicast
    Route refresh: advertised and received(old & new)
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: advertised and received
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: st01-stor-r01-u01,domain name: n/a) received (name: st01-sw25g-r01-u34,domain name: n/a)
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv4 Unicast, IPv6 Unicast
    End-of-RIB received: IPv4 Unicast, IPv6 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: False
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
    IPv4 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                  1          1
    Notifications:          0          0
    Updates:                4         45
    Keepalives:          1265       1265
    Route Refresh:          0          0
    Capability:             0          0
    Total:               1270       1311
  Minimum time between advertisement runs is 0 seconds

 For address family: IPv4 Unicast
  Update group 1, subgroup 1
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  Outbound path policy configured
  Route map for outgoing advertisements is *bgp_out
  20 accepted prefixes

 For address family: IPv6 Unicast
  Update group 2, subgroup 2
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  Outbound path policy configured
  Route map for outgoing advertisements is *bgp_out
  18 accepted prefixes

  Connections established 1; dropped 0
  Last reset 21:04:19,  Waiting for peer OPEN
Local host: fe80::1623:f2ff:fecb:86e1, Local port: 60568
Foreign host: fe80::d277:ceff:fe4b:b47a, Foreign port: 179
Nexthop: 10.10.21.21
Nexthop global: fe80::1623:f2ff:fecb:86e1
Nexthop local: fe80::1623:f2ff:fecb:86e1
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 120
Read thread: on  Write thread: on  FD used: 25



st01-stor-r01-u01# show interface
...
Interface dummy0 is up, line protocol is up
  Link ups:       0    last: (never)
  Link downs:     0    last: (never)
  vrf: default
  index 7 metric 0 mtu 9000 speed 0
  flags: <UP,BROADCAST,RUNNING,NOARP>
  Type: Ethernet
  HWaddr: ee:33:e4:bc:b8:5b
  inet 10.10.21.21/32 unnumbered
  inet6 fd0c:cc24:75a0:1:10:10:21:21/128
  inet6 fe80::ec33:e4ff:febc:b85b/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
...
Interface enp66s0f0np0 is up, line protocol is up
  Link ups:       0    last: (never)
  Link downs:     0    last: (never)
  vrf: default
  index 2 metric 0 mtu 9100 speed 25000
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: 14:23:f2:cb:86:e0
  inet6 fe80::1623:f2ff:fecb:86e0/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
  ND advertised reachable time is 0 milliseconds
  ND advertised retransmit interval is 0 milliseconds
  ND advertised hop-count limit is 64 hops
  ND router advertisements sent: 7593 rcvd: 7591
  ND router advertisements are sent every 10 seconds
  ND router advertisements lifetime tracks ra-interval
  ND router advertisement default router preference is medium
  Hosts use stateless autoconfig for addresses.
  Neighbor address(s):
  inet6 fe80::d277:ceff:fec1:6380/128
Interface enp66s0f1np1 is up, line protocol is up
  Link ups:       0    last: (never)
  Link downs:     0    last: (never)
  vrf: default
  index 3 metric 0 mtu 9100 speed 25000
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: 14:23:f2:cb:86:e1
  inet6 fe80::1623:f2ff:fecb:86e1/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
  ND advertised reachable time is 0 milliseconds
  ND advertised retransmit interval is 0 milliseconds
  ND advertised hop-count limit is 64 hops
  ND router advertisements sent: 7594 rcvd: 7591
  ND router advertisements are sent every 10 seconds
  ND router advertisements lifetime tracks ra-interval
  ND router advertisement default router preference is medium
  Hosts use stateless autoconfig for addresses.
  Neighbor address(s):
  inet6 fe80::d277:ceff:fe4b:b47a/128
...
Interface lo is up, line protocol is up
  Link ups:       0    last: (never)
  Link downs:     0    last: (never)
  vrf: default
  index 1 metric 0 mtu 65536 speed 0
  flags: <UP,LOOPBACK,RUNNING>
  Type: Loopback
  Interface Type Other
  Interface Slave Type None
  protodown: off
....
```

# Switch Networking Setup

The following section provides an insight into what the ‘Layer3-Underlay-BGP-to-the-Host’ setup looks like on the cloud
leaf switches through the output of various network commands and files.

## The configurations Files

### The Interface configuration

```bash
admin@st01-sw25g-r01-u34:~$ show interfaces status
  Interface            Lanes    Speed    MTU    FEC            Alias    Vlan    Oper    Admin             Type    Asym PFC    Oper Speed
-----------  ---------------  -------  -----  -----  ---------------  ------  ------  -------  ---------------  ----------  ------------
  Ethernet0                3      25G   9100    N/A    Eth6/3(Port1)  routed      up       up   SFP/SFP+/SFP28         N/A           25G
  Ethernet1                2      25G   9100    N/A    Eth6/2(Port2)  routed      up       up   SFP/SFP+/SFP28         N/A           25G
  Ethernet2                4      25G   9100    N/A    Eth6/4(Port3)  routed      up       up   SFP/SFP+/SFP28         N/A           25G
  Ethernet3                8      25G   9100    N/A    Eth7/4(Port4)  routed    down     down              N/A         N/A           25G
  Ethernet4                7      25G   9100    N/A    Eth7/3(Port5)  routed      up       up   SFP/SFP+/SFP28         N/A           25G
  Ethernet5                1      25G   9100    N/A    Eth6/1(Port6)  routed      up       up   SFP/SFP+/SFP28         N/A           25G
  Ethernet6                5      25G   9100    N/A    Eth7/1(Port7)  routed    down     down              N/A         N/A           25G
  Ethernet7               16      25G   9100    N/A   Eth11/4(Port8)  routed    down     down              N/A         N/A           25G
  Ethernet8                6      25G   9100    N/A    Eth7/2(Port9)  routed    down     down              N/A         N/A           25G
  Ethernet9               14      25G   9100    N/A  Eth11/2(Port10)  routed    down     down              N/A         N/A           25G
 Ethernet10               13      25G   9100    N/A  Eth11/1(Port11)  routed    down     down              N/A         N/A           25G
 Ethernet11               15      25G   9100    N/A  Eth11/3(Port12)  routed    down     down              N/A         N/A           25G
 Ethernet12               23      25G   9100    N/A  Eth18/3(Port13)  routed    down     down              N/A         N/A           25G
 Ethernet13               22      25G   9100    N/A  Eth18/2(Port14)  routed    down     down              N/A         N/A           25G
 Ethernet14               24      25G   9100    N/A  Eth18/4(Port15)  routed    down     down              N/A         N/A           25G
 Ethernet15               32      25G   9100    N/A  Eth19/4(Port16)  routed    down     down              N/A         N/A           25G
 Ethernet16               31      25G   9100    N/A  Eth19/3(Port17)  routed    down     down              N/A         N/A           25G
 Ethernet17               21      25G   9100    N/A  Eth18/1(Port18)  routed    down     down              N/A         N/A           25G
 Ethernet18               29      25G   9100    N/A  Eth19/1(Port19)  routed    down     down              N/A         N/A           25G
 Ethernet19               36      25G   9100    N/A  Eth23/4(Port20)  routed    down     down              N/A         N/A           25G
 Ethernet20               30      25G   9100    N/A  Eth19/2(Port21)  routed    down     down              N/A         N/A           25G
 Ethernet21               34      25G   9100    N/A  Eth23/2(Port22)  routed    down     down              N/A         N/A           25G
 Ethernet22               33      25G   9100    N/A  Eth23/1(Port23)  routed    down     down              N/A         N/A           25G
 Ethernet23               35      25G   9100    N/A  Eth23/3(Port24)  routed    down     down              N/A         N/A           25G
 Ethernet24               43      25G   9100    N/A  Eth30/3(Port25)  routed    down     down              N/A         N/A           25G
 Ethernet25               42      25G   9100    N/A  Eth30/2(Port26)  routed    down     down              N/A         N/A           25G
 Ethernet26               44      25G   9100    N/A  Eth30/4(Port27)  routed    down     down              N/A         N/A           25G
 Ethernet27               52      25G   9100    N/A  Eth31/4(Port28)  routed    down     down              N/A         N/A           25G
 Ethernet28               51      25G   9100    N/A  Eth31/3(Port29)  routed    down     down              N/A         N/A           25G
 Ethernet29               41      25G   9100    N/A  Eth30/1(Port30)  routed    down     down              N/A         N/A           25G
 Ethernet30               49      25G   9100    N/A  Eth31/1(Port31)  routed    down     down              N/A         N/A           25G
 Ethernet31               60      25G   9100    N/A  Eth35/4(Port32)  routed    down     down              N/A         N/A           25G
 Ethernet32               50      25G   9100    N/A  Eth31/2(Port33)  routed      up       up   SFP/SFP+/SFP28         N/A           25G
 Ethernet33               58      25G   9100    N/A  Eth35/2(Port34)  routed      up       up   SFP/SFP+/SFP28         N/A           25G
 Ethernet34               57      25G   9100    N/A  Eth35/1(Port35)  routed      up       up   SFP/SFP+/SFP28         N/A           25G
 Ethernet35               59      25G   9100    N/A  Eth35/3(Port36)  routed      up       up   SFP/SFP+/SFP28         N/A           25G
 Ethernet36               62      25G   9100    N/A  Eth42/2(Port37)  routed      up       up   SFP/SFP+/SFP28         N/A           25G
 Ethernet37               63      25G   9100    N/A  Eth42/3(Port38)  routed      up       up   SFP/SFP+/SFP28         N/A           25G
 Ethernet38               64      25G   9100    N/A  Eth42/4(Port39)  routed      up       up   SFP/SFP+/SFP28         N/A           25G
 Ethernet39               65      25G   9100    N/A  Eth40/1(Port40)  routed      up       up   SFP/SFP+/SFP28         N/A           25G
 Ethernet40               66      25G   9100    N/A  Eth40/2(Port41)  routed      up       up   SFP/SFP+/SFP28         N/A           25G
 Ethernet41               61      25G   9100    N/A  Eth42/1(Port42)  routed      up       up   SFP/SFP+/SFP28         N/A           25G
 Ethernet42               68      25G   9100    N/A  Eth40/4(Port43)  routed      up       up   SFP/SFP+/SFP28         N/A           25G
 Ethernet43               69      25G   9100    N/A  Eth44/1(Port44)  routed      up       up   SFP/SFP+/SFP28         N/A           25G
 Ethernet44               67      25G   9100    N/A  Eth40/3(Port45)  routed      up       up   SFP/SFP+/SFP28         N/A           25G
 Ethernet45               71      25G   9100    N/A  Eth44/3(Port46)  routed      up       up   SFP/SFP+/SFP28         N/A           25G
 Ethernet46               72      25G   9100    N/A  Eth44/4(Port47)  routed      up       up   SFP/SFP+/SFP28         N/A           25G
 Ethernet47               70      25G   9100    N/A  Eth44/2(Port48)  routed      up       up   SFP/SFP+/SFP28         N/A           25G
 Ethernet48      77,78,79,80     100G   9100    N/A    Eth49(Port49)  routed    down     down              N/A         N/A          100G
 Ethernet52      85,86,87,88     100G   9100    N/A    Eth50(Port50)  routed    down     down              N/A         N/A          100G
 Ethernet56      93,94,95,96     100G   9100    N/A    Eth51(Port51)  routed    down     down              N/A         N/A          100G
 Ethernet60     97,98,99,100     100G   9100    N/A    Eth52(Port52)  routed    down     down              N/A         N/A          100G
 Ethernet64  105,106,107,108     100G   9100    N/A    Eth53(Port53)  routed    down     down              N/A         N/A          100G
 Ethernet68  113,114,115,116     100G   9100    N/A    Eth54(Port54)  routed    down     down              N/A         N/A          100G
 Ethernet72  121,122,123,124     100G   9100    N/A    Eth55(Port55)  routed      up       up  QSFP28 or later         N/A          100G
 Ethernet76  125,126,127,128     100G   9100    N/A    Eth56(Port56)  routed      up       up  QSFP28 or later         N/A          100G

admin@st01-sw25g-r01-u34:~$ show ipv6 interfaces
Interface    Master    IPv4 address/mask                        Admin/Oper    BGP Neighbor    Neighbor IP
-----------  --------  ---------------------------------------  ------------  --------------  -------------
Bridge                 fe80::a0f7:67ff:fee5:6b89%Bridge/64      up/down       N/A             N/A
Ethernet0              fe80::d277:ceff:fe4b:b47a%Ethernet0/64   up/up         N/A             N/A
Ethernet1              fe80::d277:ceff:fe4b:b47a%Ethernet1/64   up/up         N/A             N/A
Ethernet2              fe80::d277:ceff:fe4b:b47a%Ethernet2/64   up/up         N/A             N/A
Ethernet4              fe80::d277:ceff:fe4b:b47a%Ethernet4/64   up/up         N/A             N/A
Ethernet5              fe80::d277:ceff:fe4b:b47a%Ethernet5/64   up/up         N/A             N/A
Ethernet32             fe80::d277:ceff:fe4b:b47a%Ethernet32/64  up/up         N/A             N/A
Ethernet33             fe80::d277:ceff:fe4b:b47a%Ethernet33/64  up/up         N/A             N/A
Ethernet34             fe80::d277:ceff:fe4b:b47a%Ethernet34/64  up/up         N/A             N/A
Ethernet35             fe80::d277:ceff:fe4b:b47a%Ethernet35/64  up/up         N/A             N/A
Ethernet36             fe80::d277:ceff:fe4b:b47a%Ethernet36/64  up/up         N/A             N/A
Ethernet37             fe80::d277:ceff:fe4b:b47a%Ethernet37/64  up/up         N/A             N/A
Ethernet38             fe80::d277:ceff:fe4b:b47a%Ethernet38/64  up/up         N/A             N/A
Ethernet39             fe80::d277:ceff:fe4b:b47a%Ethernet39/64  up/up         N/A             N/A
Ethernet40             fe80::d277:ceff:fe4b:b47a%Ethernet40/64  up/up         N/A             N/A
Ethernet41             fe80::d277:ceff:fe4b:b47a%Ethernet41/64  up/up         N/A             N/A
Ethernet42             fe80::d277:ceff:fe4b:b47a%Ethernet42/64  up/up         N/A             N/A
Ethernet43             fe80::d277:ceff:fe4b:b47a%Ethernet43/64  up/up         N/A             N/A
Ethernet44             fe80::d277:ceff:fe4b:b47a%Ethernet44/64  up/up         N/A             N/A
Ethernet45             fe80::d277:ceff:fe4b:b47a%Ethernet45/64  up/up         N/A             N/A
Ethernet46             fe80::d277:ceff:fe4b:b47a%Ethernet46/64  up/up         N/A             N/A
Ethernet47             fe80::d277:ceff:fe4b:b47a%Ethernet47/64  up/up         N/A             N/A
Ethernet72             fe80::d277:ceff:fe4b:b47a%Ethernet72/64  up/up         N/A             N/A
Ethernet76             fe80::d277:ceff:fe4b:b47a%Ethernet76/64  up/up         N/A             N/A
Loopback0              fd0c:cc24:75a0:1:10:10:21:4/128          up/up         N/A             N/A
                       fe80::4887:58ff:fe6d:3ecf%Loopback0/64                 N/A             N/A
docker0                fd00::1/80                               up/down       N/A             N/A
                       fe80::1%docker0/64                                     N/A             N/A
eth0         mgmt      fe80::d277:ceff:fe4b:b47a%eth0/64        up/up         N/A             N/A
lo                     ::1/128                                  up/up         N/A             N/A
lo-m         mgmt      fe80::d8e2:c2ff:feae:302f%lo-m/64        up/up         N/A             N/A

admin@st01-sw25g-r01-u34:~$ show ip interfaces
Interface    Master    IPv4 address/mask    Admin/Oper    BGP Neighbor    Neighbor IP
-----------  --------  -------------------  ------------  --------------  -------------
Loopback0              10.10.21.4/32        up/up         N/A             N/A
docker0                240.127.1.1/24       up/down       N/A             N/A
eth0         mgmt      10.10.23.107/24      up/up         N/A             N/A
lo                     127.0.0.1/16         up/up         N/A             N/A
lo-m         mgmt      127.0.0.1/16         up/up         N/A             N/A

admin@st01-sw25g-r01-u34:~$ show ip route
Codes: K - kernel route, C - connected, S - static, R - RIP,
       O - OSPF, I - IS-IS, B - BGP, E - EIGRP, N - NHRP,
       T - Table, v - VNC, V - VNC-Direct, A - Babel, F - PBR,
       f - OpenFabric,
       > - selected route, * - FIB route, q - queued, r - rejected, b - backup
       t - trapped, o - offload failure

C>* 10.10.21.4/32 is directly connected, Loopback0, 03w2d19h
B>* 10.10.21.5/32 [20/0] via fe80::922d:77ff:fe58:2650, Ethernet72, weight 1, 03w2d19h
  *                      via fe80::922d:77ff:fe58:2750, Ethernet76, weight 1, 03w2d19h
B>* 10.10.21.6/32 [20/0] via fe80::922d:77ff:fe58:2650, Ethernet72, weight 1, 03w2d19h
  *                      via fe80::922d:77ff:fe58:2750, Ethernet76, weight 1, 03w2d19h
B>* 10.10.21.7/32 [20/0] via fe80::922d:77ff:fe58:2650, Ethernet72, weight 1, 03w2d19h
  *                      via fe80::922d:77ff:fe58:2750, Ethernet76, weight 1, 03w2d19h
B>* 10.10.21.10/32 [20/0] via fe80::5e6f:69ff:feb0:49c1, Ethernet5, weight 1, 02w0d17h
B>* 10.10.21.11/32 [20/0] via fe80::1623:f3ff:fef5:6101, Ethernet4, weight 1, 02w3d01h
B>* 10.10.21.12/32 [20/0] via fe80::5e6f:69ff:feb0:4b61, Ethernet2, weight 1, 19:35:05
B>* 10.10.21.13/32 [20/0] via fe80::5e6f:69ff:feb0:4b41, Ethernet1, weight 1, 02w1d23h
B>* 10.10.21.14/32 [20/0] via fe80::5e6f:69ff:feb0:46f1, Ethernet0, weight 1, 02w3d01h
B>* 10.10.21.21/32 [20/0] via fe80::1623:f2ff:fecb:86e1, Ethernet47, weight 1, 21:32:59
B>* 10.10.21.22/32 [20/0] via fe80::1623:f2ff:fecb:c0b1, Ethernet46, weight 1, 02w3d01h
B>* 10.10.21.23/32 [20/0] via fe80::1623:f2ff:fecb:cc41, Ethernet45, weight 1, 02w3d01h
B>* 10.10.21.24/32 [20/0] via fe80::1623:f2ff:fecb:c0f1, Ethernet44, weight 1, 02w3d01h
B>* 10.10.21.25/32 [20/0] via fe80::5e6f:69ff:feb0:bc81, Ethernet43, weight 1, 02w2d23h
B>* 10.10.21.26/32 [20/0] via fe80::5e6f:69ff:feb0:c461, Ethernet42, weight 1, 02w6d18h
B>* 10.10.21.27/32 [20/0] via fe80::1623:f2ff:fecb:a9a1, Ethernet41, weight 1, 02w6d18h
B>* 10.10.21.28/32 [20/0] via fe80::5e6f:69ff:feb0:c451, Ethernet40, weight 1, 02w3d02h
B>* 10.10.21.29/32 [20/0] via fe80::1623:f2ff:fecb:b381, Ethernet39, weight 1, 02w3d01h
B>* 10.10.21.30/32 [20/0] via fe80::5e6f:69ff:feb0:c0f1, Ethernet38, weight 1, 02w3d01h
B>* 10.10.21.200/32 [20/0] via fe80::5e6f:69ff:feb0:4b41, Ethernet1, weight 1, 19:38:44
B>* 10.10.21.201/32 [20/0] via fe80::5e6f:69ff:feb0:4b41, Ethernet1, weight 1, 19:38:44

```

### The configuration of the FRRouting Daemon

See also the [backups of the switch configuration files](../device_configurations/network).

```bash
admin@st01-sw25g-r01-u34:~$ vtysh

Hello, this is FRRouting (version 8.1).
Copyright 1996-2005 Kunihiro Ishiguro, et al.

st01-sw25g-r01-u34# show running-config
Building configuration...

Current configuration:
!
frr version 8.1
frr defaults traditional
hostname st01-sw25g-r01-u34
service integrated-vtysh-config
!
router bgp 65404
 bgp router-id 10.10.21.4
 bgp log-neighbor-changes
 bgp always-compare-med
 no bgp ebgp-requires-policy
 neighbor core peer-group
 neighbor core remote-as 65501
 neighbor server peer-group
 neighbor server remote-as external
 neighbor Ethernet72 interface peer-group core
 neighbor Ethernet76 interface peer-group core
 neighbor Ethernet0 interface peer-group server
 neighbor Ethernet1 interface peer-group server
 neighbor Ethernet2 interface peer-group server
 neighbor Ethernet4 interface peer-group server
 neighbor Ethernet5 interface peer-group server
 neighbor Ethernet38 interface peer-group server
 neighbor Ethernet39 interface peer-group server
 neighbor Ethernet40 interface peer-group server
 neighbor Ethernet41 interface peer-group server
 neighbor Ethernet42 interface peer-group server
 neighbor Ethernet43 interface peer-group server
 neighbor Ethernet44 interface peer-group server
 neighbor Ethernet45 interface peer-group server
 neighbor Ethernet46 interface peer-group server
 neighbor Ethernet47 interface peer-group server
 !
 address-family ipv4 unicast
  network 10.10.21.4/32
 exit-address-family
 !
 address-family ipv6 unicast
  network fd0c:cc24:75a0:1:10:10:21:4/128
  neighbor core activate
  neighbor server activate
 exit-address-family
exit
!
route-map RM_SET_SRC6 permit 10
 set src fd0c:cc24:75a0:1:10:10:21:4
exit
!
route-map RM_SET_SRC permit 10
 set src 10.10.21.4
exit
!
ip protocol bgp route-map RM_SET_SRC
!
ipv6 protocol bgp route-map RM_SET_SRC6
!
end

```

## Output of the disagnostic tools


### Interfaces

```bash
admin@st01-sw25g-r01-u34:~$ ip link ls
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq master mgmt state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
3: eth1: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7b brd ff:ff:ff:ff:ff:ff
4: eth2: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7c brd ff:ff:ff:ff:ff:ff
5: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN mode DEFAULT group default
    link/ether 02:42:51:42:30:22 brd ff:ff:ff:ff:ff:ff
8: bcm0: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether 02:10:18:de:fe:4a brd ff:ff:ff:ff:ff:ff
11: Ethernet5: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
12: Ethernet1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
13: Ethernet0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
14: Ethernet2: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
15: Ethernet6: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
16: Ethernet8: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
17: Ethernet4: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
18: Ethernet3: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
19: Ethernet10: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
20: Ethernet9: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
21: Ethernet11: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
22: Ethernet7: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
23: Ethernet17: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
24: Ethernet13: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
25: Ethernet12: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
26: Ethernet14: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
27: Ethernet18: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
28: Ethernet20: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
29: Ethernet16: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
30: Ethernet15: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
31: Ethernet22: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
32: Ethernet21: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
33: Ethernet23: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
34: Ethernet19: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
35: Ethernet29: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
36: Ethernet25: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
37: Ethernet24: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
38: Ethernet26: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
39: Ethernet30: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
40: Ethernet32: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
41: Ethernet28: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
42: Ethernet27: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
43: Ethernet34: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
44: Ethernet33: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
45: Ethernet35: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
46: Ethernet31: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
47: Ethernet41: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
48: Ethernet36: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
49: Ethernet37: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
50: Ethernet38: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
51: Ethernet39: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
52: Ethernet40: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
53: Ethernet44: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
54: Ethernet42: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
55: Ethernet43: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
56: Bridge: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 9100 qdisc noqueue state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
57: dummy: <BROADCAST,NOARP> mtu 1500 qdisc noop master Bridge state DOWN mode DEFAULT group default qlen 1000
    link/ether 9e:7b:9d:26:ff:7b brd ff:ff:ff:ff:ff:ff
58: Ethernet47: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
59: Ethernet45: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
60: Ethernet46: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
61: Ethernet48: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
62: Ethernet52: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
63: Loopback0: <BROADCAST,NOARP,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/ether 4a:87:58:6d:3e:cf brd ff:ff:ff:ff:ff:ff
64: Ethernet56: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
65: Ethernet60: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
66: Ethernet64: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
67: Ethernet68: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
68: Ethernet72: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
69: Ethernet76: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
70: pimreg@NONE: <NOARP,UP,LOWER_UP> mtu 1472 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/pimreg
71: pimreg5000@NONE: <NOARP,ALLMULTI> mtu 1472 qdisc noqueue state DOWN mode DEFAULT group default qlen 1000
    link/pimreg
72: mgmt: <NOARP,MASTER,UP,LOWER_UP> mtu 65575 qdisc noqueue state UP mode DEFAULT group default qlen 1000
    link/ether aa:e0:85:9e:aa:ea brd ff:ff:ff:ff:ff:ff
73: lo-m: <BROADCAST,NOARP,UP,LOWER_UP> mtu 1500 qdisc noqueue master mgmt state UNKNOWN mode DEFAULT group default qlen 1000
    link/ether da:e2:c2:ae:30:2f brd ff:ff:ff:ff:ff:ff


admin@st01-sw25g-r01-u34:~$ ip addr ls
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/16 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq master mgmt state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet 10.10.23.107/24 brd 10.10.23.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
3: eth1: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7b brd ff:ff:ff:ff:ff:ff
4: eth2: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7c brd ff:ff:ff:ff:ff:ff
5: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN group default
    link/ether 02:42:51:42:30:22 brd ff:ff:ff:ff:ff:ff
    inet 240.127.1.1/24 brd 240.127.1.255 scope global docker0
       valid_lft forever preferred_lft forever
    inet6 fd00::1/80 scope global
       valid_lft forever preferred_lft forever
    inet6 fe80::1/64 scope link
       valid_lft forever preferred_lft forever
8: bcm0: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether 02:10:18:de:fe:4a brd ff:ff:ff:ff:ff:ff
11: Ethernet5: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
12: Ethernet1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
13: Ethernet0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
14: Ethernet2: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
15: Ethernet6: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
16: Ethernet8: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
17: Ethernet4: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
18: Ethernet3: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
19: Ethernet10: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
20: Ethernet9: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
21: Ethernet11: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
22: Ethernet7: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
23: Ethernet17: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
24: Ethernet13: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
25: Ethernet12: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
26: Ethernet14: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
27: Ethernet18: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
28: Ethernet20: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
29: Ethernet16: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
30: Ethernet15: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
31: Ethernet22: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
32: Ethernet21: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
33: Ethernet23: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
34: Ethernet19: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
35: Ethernet29: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
36: Ethernet25: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
37: Ethernet24: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
38: Ethernet26: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
39: Ethernet30: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
40: Ethernet32: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
41: Ethernet28: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
42: Ethernet27: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
43: Ethernet34: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
44: Ethernet33: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
45: Ethernet35: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
46: Ethernet31: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
47: Ethernet41: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
48: Ethernet36: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
49: Ethernet37: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
50: Ethernet38: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
51: Ethernet39: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
52: Ethernet40: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
53: Ethernet44: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
54: Ethernet42: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
55: Ethernet43: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
56: Bridge: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 9100 qdisc noqueue state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::a0f7:67ff:fee5:6b89/64 scope link
       valid_lft forever preferred_lft forever
57: dummy: <BROADCAST,NOARP> mtu 1500 qdisc noop master Bridge state DOWN group default qlen 1000
    link/ether 9e:7b:9d:26:ff:7b brd ff:ff:ff:ff:ff:ff
58: Ethernet47: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
59: Ethernet45: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
60: Ethernet46: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
61: Ethernet48: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
62: Ethernet52: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
63: Loopback0: <BROADCAST,NOARP,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/ether 4a:87:58:6d:3e:cf brd ff:ff:ff:ff:ff:ff
    inet 10.10.21.4/32 scope global Loopback0
       valid_lft forever preferred_lft forever
    inet6 fd0c:cc24:75a0:1:10:10:21:4/128 scope global
       valid_lft forever preferred_lft forever
    inet6 fe80::4887:58ff:fe6d:3ecf/64 scope link
       valid_lft forever preferred_lft forever
64: Ethernet56: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
65: Ethernet60: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
66: Ethernet64: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
67: Ethernet68: <BROADCAST,MULTICAST> mtu 9100 qdisc noop state DOWN group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
68: Ethernet72: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
69: Ethernet76: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9100 qdisc pfifo_fast state UP group default qlen 1000
    link/ether d0:77:ce:4b:b4:7a brd ff:ff:ff:ff:ff:ff
    inet6 fe80::d277:ceff:fe4b:b47a/64 scope link
       valid_lft forever preferred_lft forever
70: pimreg@NONE: <NOARP,UP,LOWER_UP> mtu 1472 qdisc noqueue state UNKNOWN group default qlen 1000
    link/pimreg
71: pimreg5000@NONE: <NOARP,ALLMULTI> mtu 1472 qdisc noqueue state DOWN group default qlen 1000
    link/pimreg
72: mgmt: <NOARP,MASTER,UP,LOWER_UP> mtu 65575 qdisc noqueue state UP group default qlen 1000
    link/ether aa:e0:85:9e:aa:ea brd ff:ff:ff:ff:ff:ff
73: lo-m: <BROADCAST,NOARP,UP,LOWER_UP> mtu 1500 qdisc noqueue master mgmt state UNKNOWN group default qlen 1000
    link/ether da:e2:c2:ae:30:2f brd ff:ff:ff:ff:ff:ff
    inet 127.0.0.1/16 scope host lo-m
       valid_lft forever preferred_lft forever
    inet6 fe80::d8e2:c2ff:feae:302f/64 scope link
       valid_lft forever preferred_lft forever

```

### Routing

**FRRouting status**

```bash
admin@st01-sw25g-r01-u34:~$ vtysh

Hello, this is FRRouting (version 8.1).
Copyright 1996-2005 Kunihiro Ishiguro, et al.

st01-sw25g-r01-u34# show ip bgp summary

IPv4 Unicast Summary (VRF default):
BGP router identifier 10.10.21.4, local AS number 65404 vrf-id 0
BGP table version 142
RIB entries 41, using 7544 bytes of memory
Peers 17, using 12 MiB of memory
Peer groups 2, using 128 bytes of memory

Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
Ethernet72      4      65501     34601     34529        0    0    0 03w2d19h            6       21 N/A
Ethernet76      4      65501     34605     34529        0    0    0 03w2d19h            6       21 N/A
Ethernet0       4 4210021014     34305     34611        0    0    0 02w3d01h            3       21 N/A
Ethernet1       4 4210021013     34264     34548        0    0    0 02w1d22h            3       21 N/A
Ethernet2       4 4210021012     34316     34686        0    0    0 19:20:07            3       21 N/A
Ethernet4       4 4210021011     34306     34614        0    0    0 02w3d01h            1       21 N/A
Ethernet5       4 4210021010     34315     34618        0    0    0 02w0d17h            1       21 N/A
Ethernet38      4 4210021030     34298     34567        0    0    0 02w3d01h            1       21 N/A
Ethernet39      4 4210021029     34299     34561        0    0    0 02w3d01h            1       21 N/A
Ethernet40      4 4210021028     34299     34592        0    0    0 02w3d01h            1       21 N/A
Ethernet41      4 4210021027     34301     34554        0    0    0 02w6d18h            1       21 N/A
Ethernet42      4 4210021026     34301     34590        0    0    0 02w6d18h            1       21 N/A
Ethernet43      4 4210021025     34305     34551        0    0    0 02w6d18h            1       21 N/A
Ethernet44      4 4210021024     34299     34576        0    0    0 02w3d01h            1       21 N/A
Ethernet45      4 4210021023     34298     34571        0    0    0 02w3d01h            1       21 N/A
Ethernet46      4 4210021022     34306     34619        0    0    0 02w3d01h            1       21 N/A
Ethernet47      4 4210021021     34311     34655        0    0    0 21:18:00            1       21 N/A

Total number of neighbors 17

st01-sw25g-r01-u34# show ip route
Codes: K - kernel route, C - connected, S - static, R - RIP,
       O - OSPF, I - IS-IS, B - BGP, E - EIGRP, N - NHRP,
       T - Table, v - VNC, V - VNC-Direct, A - Babel, F - PBR,
       f - OpenFabric,
       > - selected route, * - FIB route, q - queued, r - rejected, b - backup
       t - trapped, o - offload failure

C>* 10.10.21.4/32 is directly connected, Loopback0, 03w2d19h
B>* 10.10.21.5/32 [20/0] via fe80::922d:77ff:fe58:2650, Ethernet72, weight 1, 03w2d19h
  *                      via fe80::922d:77ff:fe58:2750, Ethernet76, weight 1, 03w2d19h
B>* 10.10.21.6/32 [20/0] via fe80::922d:77ff:fe58:2650, Ethernet72, weight 1, 03w2d19h
  *                      via fe80::922d:77ff:fe58:2750, Ethernet76, weight 1, 03w2d19h
B>* 10.10.21.7/32 [20/0] via fe80::922d:77ff:fe58:2650, Ethernet72, weight 1, 03w2d19h
  *                      via fe80::922d:77ff:fe58:2750, Ethernet76, weight 1, 03w2d19h
B>* 10.10.21.10/32 [20/0] via fe80::5e6f:69ff:feb0:49c1, Ethernet5, weight 1, 02w0d17h
B>* 10.10.21.11/32 [20/0] via fe80::1623:f3ff:fef5:6101, Ethernet4, weight 1, 02w3d01h
B>* 10.10.21.12/32 [20/0] via fe80::5e6f:69ff:feb0:4b61, Ethernet2, weight 1, 19:20:42
B>* 10.10.21.13/32 [20/0] via fe80::5e6f:69ff:feb0:4b41, Ethernet1, weight 1, 02w1d22h
B>* 10.10.21.14/32 [20/0] via fe80::5e6f:69ff:feb0:46f1, Ethernet0, weight 1, 02w3d01h
B>* 10.10.21.21/32 [20/0] via fe80::1623:f2ff:fecb:86e1, Ethernet47, weight 1, 21:18:36
B>* 10.10.21.22/32 [20/0] via fe80::1623:f2ff:fecb:c0b1, Ethernet46, weight 1, 02w3d01h
B>* 10.10.21.23/32 [20/0] via fe80::1623:f2ff:fecb:cc41, Ethernet45, weight 1, 02w3d01h
B>* 10.10.21.24/32 [20/0] via fe80::1623:f2ff:fecb:c0f1, Ethernet44, weight 1, 02w3d01h
B>* 10.10.21.25/32 [20/0] via fe80::5e6f:69ff:feb0:bc81, Ethernet43, weight 1, 02w2d23h
B>* 10.10.21.26/32 [20/0] via fe80::5e6f:69ff:feb0:c461, Ethernet42, weight 1, 02w6d18h
B>* 10.10.21.27/32 [20/0] via fe80::1623:f2ff:fecb:a9a1, Ethernet41, weight 1, 02w6d18h
B>* 10.10.21.28/32 [20/0] via fe80::5e6f:69ff:feb0:c451, Ethernet40, weight 1, 02w3d01h
B>* 10.10.21.29/32 [20/0] via fe80::1623:f2ff:fecb:b381, Ethernet39, weight 1, 02w3d01h
B>* 10.10.21.30/32 [20/0] via fe80::5e6f:69ff:feb0:c0f1, Ethernet38, weight 1, 02w3d01h
B>* 10.10.21.200/32 [20/0] via fe80::5e6f:69ff:feb0:4b41, Ethernet1, weight 1, 19:24:21
B>* 10.10.21.201/32 [20/0] via fe80::5e6f:69ff:feb0:4b41, Ethernet1, weight 1, 19:24:21


st01-sw25g-r01-u34# show ip bgp neighbors
BGP neighbor on Ethernet72: fe80::922d:77ff:fe58:2650, remote AS 65501, local AS 65404, external link
Hostname: sonic
 Member of peer-group core for session parameters
  BGP version 4, remote router ID 10.10.21.7, local router ID 10.10.21.4
  BGP state = Established, up for 03w2d19h
  Last read 00:00:21, Last write 00:00:23
  Hold time is 180, keepalive interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv4 Unicast: RX advertised and received
      IPv6 Unicast: RX advertised and received
    Extended nexthop: advertised and received
      Address families by peer:
                   IPv4 Unicast
    Route refresh: advertised and received(old & new)
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: advertised and received
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: st01-sw25g-r01-u34,domain name: n/a) received (name: sonic,domain name: n/a)
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv4 Unicast, IPv6 Unicast
    End-of-RIB received: IPv4 Unicast, IPv6 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: True
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
    IPv4 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                  1          1
    Notifications:          0          0
    Updates:              246        318
    Keepalives:         34283      34283
    Route Refresh:          0          0
    Capability:             0          0
    Total:              34530      34602
  Minimum time between advertisement runs is 0 seconds

 For address family: IPv4 Unicast
  core peer-group member
  Update group 1, subgroup 3
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  6 accepted prefixes

 For address family: IPv6 Unicast
  core peer-group member
  Update group 2, subgroup 4
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  4 accepted prefixes

  Connections established 1; dropped 0
  Last reset 03w2d19h,  Waiting for peer OPEN
Local host: fe80::d277:ceff:fe4b:b47a, Local port: 35784
Foreign host: fe80::922d:77ff:fe58:2650, Foreign port: 179
Nexthop: 10.10.21.4
Nexthop global: fe80::d277:ceff:fe4b:b47a
Nexthop local: fe80::d277:ceff:fe4b:b47a
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 120
Read thread: on  Write thread: on  FD used: 23

BGP neighbor on Ethernet76: fe80::922d:77ff:fe58:2750, remote AS 65501, local AS 65404, external link
Hostname: sonic
 Member of peer-group core for session parameters
  BGP version 4, remote router ID 10.10.21.6, local router ID 10.10.21.4
  BGP state = Established, up for 03w2d19h
  Last read 00:00:16, Last write 00:00:18
  Hold time is 180, keepalive interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv4 Unicast: RX advertised and received
      IPv6 Unicast: RX advertised and received
    Extended nexthop: advertised and received
      Address families by peer:
                   IPv4 Unicast
    Route refresh: advertised and received(old & new)
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: advertised and received
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: st01-sw25g-r01-u34,domain name: n/a) received (name: sonic,domain name: n/a)
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv4 Unicast, IPv6 Unicast
    End-of-RIB received: IPv4 Unicast, IPv6 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: True
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
    IPv4 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                  1          1
    Notifications:          0          0
    Updates:              246        322
    Keepalives:         34283      34283
    Route Refresh:          0          0
    Capability:             0          0
    Total:              34530      34606
  Minimum time between advertisement runs is 0 seconds

 For address family: IPv4 Unicast
  core peer-group member
  Update group 1, subgroup 3
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  6 accepted prefixes

 For address family: IPv6 Unicast
  core peer-group member
  Update group 2, subgroup 4
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  4 accepted prefixes

  Connections established 1; dropped 0
  Last reset 03w2d19h,  Waiting for peer OPEN
Local host: fe80::d277:ceff:fe4b:b47a, Local port: 45778
Foreign host: fe80::922d:77ff:fe58:2750, Foreign port: 179
Nexthop: 10.10.21.4
Nexthop global: fe80::d277:ceff:fe4b:b47a
Nexthop local: fe80::d277:ceff:fe4b:b47a
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 120
Read thread: on  Write thread: on  FD used: 27

BGP neighbor on Ethernet0: fe80::5e6f:69ff:feb0:46f1, remote AS 4210021014, local AS 65404, external link
Hostname: st01-ctl-r01-u29
 Member of peer-group server for session parameters
  BGP version 4, remote router ID 10.10.21.14, local router ID 10.10.21.4
  BGP state = Established, up for 02w3d01h
  Last read 00:00:44, Last write 00:00:46
  Hold time is 180, keepalive interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv4 Unicast: RX advertised and received
      IPv6 Unicast: RX advertised and received
    Extended nexthop: advertised and received
      Address families by peer:
                   IPv4 Unicast
    Route refresh: advertised and received(old & new)
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: advertised and received
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: st01-sw25g-r01-u34,domain name: n/a) received (name: st01-ctl-r01-u29,domain name: n/a)
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv4 Unicast, IPv6 Unicast
    End-of-RIB received: IPv4 Unicast, IPv6 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: True
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
    IPv4 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                  8          4
    Notifications:          0          6
    Updates:              324         16
    Keepalives:         34280      34280
    Route Refresh:          0          0
    Capability:             0          0
    Total:              34612      34306
  Minimum time between advertisement runs is 0 seconds

 For address family: IPv4 Unicast
  server peer-group member
  Update group 3, subgroup 5
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  3 accepted prefixes

 For address family: IPv6 Unicast
  server peer-group member
  Update group 4, subgroup 6
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

  Connections established 4; dropped 3
  Last reset 02w3d01h,  No AFI/SAFI activated for peer
Local host: fe80::d277:ceff:fe4b:b47a, Local port: 179
Foreign host: fe80::5e6f:69ff:feb0:46f1, Foreign port: 57296
Nexthop: 10.10.21.4
Nexthop global: fe80::d277:ceff:fe4b:b47a
Nexthop local: fe80::d277:ceff:fe4b:b47a
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 120
Read thread: on  Write thread: on  FD used: 35

BGP neighbor on Ethernet1: fe80::5e6f:69ff:feb0:4b41, remote AS 4210021013, local AS 65404, external link
Hostname: st01-ctl-r01-u28
 Member of peer-group server for session parameters
  BGP version 4, remote router ID 10.10.21.13, local router ID 10.10.21.4
  BGP state = Established, up for 02w1d22h
  Last read 00:00:32, Last write 00:00:31
  Hold time is 180, keepalive interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv4 Unicast: RX advertised and received
      IPv6 Unicast: RX advertised and received
    Extended nexthop: advertised and received
      Address families by peer:
                   IPv4 Unicast
    Route refresh: advertised and received(old & new)
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: advertised and received
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: st01-sw25g-r01-u34,domain name: n/a) received (name: st01-ctl-r01-u28,domain name: n/a)
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv4 Unicast, IPv6 Unicast
    End-of-RIB received: IPv4 Unicast, IPv6 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: False
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
    IPv4 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                  6          4
    Notifications:          0          4
    Updates:              302         16
    Keepalives:         34241      34241
    Route Refresh:          0          0
    Capability:             0          0
    Total:              34549      34265
  Minimum time between advertisement runs is 0 seconds

 For address family: IPv4 Unicast
  server peer-group member
  Update group 3, subgroup 5
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  3 accepted prefixes

 For address family: IPv6 Unicast
  server peer-group member
  Update group 4, subgroup 6
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

  Connections established 4; dropped 3
  Last reset 02w1d22h,  Waiting for peer OPEN
Local host: fe80::d277:ceff:fe4b:b47a, Local port: 51562
Foreign host: fe80::5e6f:69ff:feb0:4b41, Foreign port: 179
Nexthop: 10.10.21.4
Nexthop global: fe80::d277:ceff:fe4b:b47a
Nexthop local: fe80::d277:ceff:fe4b:b47a
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 120
Read thread: on  Write thread: on  FD used: 40

BGP neighbor on Ethernet2: fe80::5e6f:69ff:feb0:4b61, remote AS 4210021012, local AS 65404, external link
Hostname: st01-ctl-r01-u27
 Member of peer-group server for session parameters
  BGP version 4, remote router ID 10.10.21.12, local router ID 10.10.21.4
  BGP state = Established, up for 19:21:19
  Last read 00:00:19, Last write 00:00:18
  Hold time is 180, keepalive interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv4 Unicast: RX advertised and received
      IPv6 Unicast: RX advertised and received
    Extended nexthop: advertised and received
      Address families by peer:
                   IPv4 Unicast
    Route refresh: advertised and received(old & new)
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: advertised and received
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: st01-sw25g-r01-u34,domain name: n/a) received (name: st01-ctl-r01-u27,domain name: n/a)
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv4 Unicast, IPv6 Unicast
    End-of-RIB received: IPv4 Unicast, IPv6 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: True
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
    IPv4 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                 11          6
    Notifications:          0         10
    Updates:              398         24
    Keepalives:         34278      34277
    Route Refresh:          0          0
    Capability:             0          0
    Total:              34687      34317
  Minimum time between advertisement runs is 0 seconds

 For address family: IPv4 Unicast
  server peer-group member
  Update group 3, subgroup 5
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  3 accepted prefixes

 For address family: IPv6 Unicast
  server peer-group member
  Update group 4, subgroup 6
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

  Connections established 6; dropped 5
  Last reset 19:24:53,  Waiting for peer OPEN
Local host: fe80::d277:ceff:fe4b:b47a, Local port: 38360
Foreign host: fe80::5e6f:69ff:feb0:4b61, Foreign port: 179
Nexthop: 10.10.21.4
Nexthop global: fe80::d277:ceff:fe4b:b47a
Nexthop local: fe80::d277:ceff:fe4b:b47a
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 120
Read thread: on  Write thread: on  FD used: 37

BGP neighbor on Ethernet4: fe80::1623:f3ff:fef5:6101, remote AS 4210021011, local AS 65404, external link
Hostname: st01-mgmt-r01-u31
 Member of peer-group server for session parameters
  BGP version 4, remote router ID 10.10.21.11, local router ID 10.10.21.4
  BGP state = Established, up for 02w3d01h
  Last read 00:00:05, Last write 00:00:06
  Hold time is 180, keepalive interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv4 Unicast: RX advertised and received
      IPv6 Unicast: RX advertised and received
    Extended nexthop: advertised and received
      Address families by peer:
                   IPv4 Unicast
    Route refresh: advertised and received(old & new)
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: advertised and received
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: st01-sw25g-r01-u34,domain name: n/a) received (name: st01-mgmt-r01-u31,domain name: n/a)
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv4 Unicast, IPv6 Unicast
    End-of-RIB received: IPv4 Unicast, IPv6 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: True
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
    IPv4 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                  8          4
    Notifications:          0          6
    Updates:              326         16
    Keepalives:         34282      34282
    Route Refresh:          0          0
    Capability:             0          0
    Total:              34616      34308
  Minimum time between advertisement runs is 0 seconds

 For address family: IPv4 Unicast
  server peer-group member
  Update group 3, subgroup 5
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

 For address family: IPv6 Unicast
  server peer-group member
  Update group 4, subgroup 6
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

  Connections established 4; dropped 3
  Last reset 02w3d01h,  No AFI/SAFI activated for peer
Local host: fe80::d277:ceff:fe4b:b47a, Local port: 179
Foreign host: fe80::1623:f3ff:fef5:6101, Foreign port: 53786
Nexthop: 10.10.21.4
Nexthop global: fe80::d277:ceff:fe4b:b47a
Nexthop local: fe80::d277:ceff:fe4b:b47a
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 120
Read thread: on  Write thread: on  FD used: 36

BGP neighbor on Ethernet5: fe80::5e6f:69ff:feb0:49c1, remote AS 4210021010, local AS 65404, external link
Hostname: st01-mgmt-r01-u30
 Member of peer-group server for session parameters
  BGP version 4, remote router ID 10.10.21.10, local router ID 10.10.21.4
  BGP state = Established, up for 02w0d17h
  Last read 00:00:40, Last write 00:00:41
  Hold time is 180, keepalive interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv4 Unicast: RX advertised and received
      IPv6 Unicast: RX advertised and received
    Extended nexthop: advertised and received
      Address families by peer:
                   IPv4 Unicast
    Route refresh: advertised and received(old & new)
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: advertised and received
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: st01-sw25g-r01-u34,domain name: n/a) received (name: st01-mgmt-r01-u30,domain name: n/a)
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv4 Unicast, IPv6 Unicast
    End-of-RIB received: IPv4 Unicast, IPv6 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: True
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
    IPv4 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                  7          4
    Notifications:          0          6
    Updates:              338         32
    Keepalives:         34274      34274
    Route Refresh:          0          0
    Capability:             0          0
    Total:              34619      34316
  Minimum time between advertisement runs is 0 seconds

 For address family: IPv4 Unicast
  server peer-group member
  Update group 3, subgroup 5
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

 For address family: IPv6 Unicast
  server peer-group member
  Update group 4, subgroup 6
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

  Connections established 4; dropped 3
  Last reset 02w0d17h,  No AFI/SAFI activated for peer
Local host: fe80::d277:ceff:fe4b:b47a, Local port: 179
Foreign host: fe80::5e6f:69ff:feb0:49c1, Foreign port: 40152
Nexthop: 10.10.21.4
Nexthop global: fe80::d277:ceff:fe4b:b47a
Nexthop local: fe80::d277:ceff:fe4b:b47a
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 120
Read thread: on  Write thread: on  FD used: 31

BGP neighbor on Ethernet38: fe80::5e6f:69ff:feb0:c0f1, remote AS 4210021030, local AS 65404, external link
Hostname: st01-comp-r01-u19
 Member of peer-group server for session parameters
  BGP version 4, remote router ID 10.10.21.30, local router ID 10.10.21.4
  BGP state = Established, up for 02w3d01h
  Last read 00:00:01, Last write 00:00:03
  Hold time is 180, keepalive interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv4 Unicast: RX advertised and received
      IPv6 Unicast: RX advertised and received
    Extended nexthop: advertised and received
      Address families by peer:
                   IPv4 Unicast
    Route refresh: advertised and received(old & new)
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: advertised and received
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: st01-sw25g-r01-u34,domain name: n/a) received (name: st01-comp-r01-u19,domain name: n/a)
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv4 Unicast, IPv6 Unicast
    End-of-RIB received: IPv4 Unicast, IPv6 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: True
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
    IPv4 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                  6          3
    Notifications:          0          4
    Updates:              282         12
    Keepalives:         34281      34281
    Route Refresh:          0          0
    Capability:             0          0
    Total:              34569      34300
  Minimum time between advertisement runs is 0 seconds

 For address family: IPv4 Unicast
  server peer-group member
  Update group 3, subgroup 5
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

 For address family: IPv6 Unicast
  server peer-group member
  Update group 4, subgroup 6
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

  Connections established 3; dropped 2
  Last reset 02w3d01h,  No AFI/SAFI activated for peer
Local host: fe80::d277:ceff:fe4b:b47a, Local port: 179
Foreign host: fe80::5e6f:69ff:feb0:c0f1, Foreign port: 37732
Nexthop: 10.10.21.4
Nexthop global: fe80::d277:ceff:fe4b:b47a
Nexthop local: fe80::d277:ceff:fe4b:b47a
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 120
Read thread: on  Write thread: on  FD used: 41

BGP neighbor on Ethernet39: fe80::1623:f2ff:fecb:b381, remote AS 4210021029, local AS 65404, external link
Hostname: st01-comp-r01-u17
 Member of peer-group server for session parameters
  BGP version 4, remote router ID 10.10.21.29, local router ID 10.10.21.4
  BGP state = Established, up for 02w3d01h
  Last read 00:00:23, Last write 00:00:24
  Hold time is 180, keepalive interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv4 Unicast: RX advertised and received
      IPv6 Unicast: RX advertised and received
    Extended nexthop: advertised and received
      Address families by peer:
                   IPv4 Unicast
    Route refresh: advertised and received(old & new)
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: advertised and received
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: st01-sw25g-r01-u34,domain name: n/a) received (name: st01-comp-r01-u17,domain name: n/a)
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv4 Unicast, IPv6 Unicast
    End-of-RIB received: IPv4 Unicast, IPv6 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: True
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
    IPv4 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                  6          3
    Notifications:          0          4
    Updates:              275         12
    Keepalives:         34281      34281
    Route Refresh:          0          0
    Capability:             0          0
    Total:              34562      34300
  Minimum time between advertisement runs is 0 seconds

 For address family: IPv4 Unicast
  server peer-group member
  Update group 3, subgroup 5
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

 For address family: IPv6 Unicast
  server peer-group member
  Update group 4, subgroup 6
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

  Connections established 3; dropped 2
  Last reset 02w3d01h,  No AFI/SAFI activated for peer
Local host: fe80::d277:ceff:fe4b:b47a, Local port: 179
Foreign host: fe80::1623:f2ff:fecb:b381, Foreign port: 47994
Nexthop: 10.10.21.4
Nexthop global: fe80::d277:ceff:fe4b:b47a
Nexthop local: fe80::d277:ceff:fe4b:b47a
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 120
Read thread: on  Write thread: on  FD used: 39

BGP neighbor on Ethernet40: fe80::5e6f:69ff:feb0:c451, remote AS 4210021028, local AS 65404, external link
Hostname: st01-comp-r01-u15
 Member of peer-group server for session parameters
  BGP version 4, remote router ID 10.10.21.28, local router ID 10.10.21.4
  BGP state = Established, up for 02w3d01h
  Last read 00:00:27, Last write 00:00:27
  Hold time is 180, keepalive interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv4 Unicast: RX advertised and received
      IPv6 Unicast: RX advertised and received
    Extended nexthop: advertised and received
      Address families by peer:
                   IPv4 Unicast
    Route refresh: advertised and received(old & new)
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: advertised and received
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: st01-sw25g-r01-u34,domain name: n/a) received (name: st01-comp-r01-u15,domain name: n/a)
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv4 Unicast, IPv6 Unicast
    End-of-RIB received: IPv4 Unicast, IPv6 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: True
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
    IPv4 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                  6          3
    Notifications:          0          4
    Updates:              306         12
    Keepalives:         34281      34281
    Route Refresh:          0          0
    Capability:             0          0
    Total:              34593      34300
  Minimum time between advertisement runs is 0 seconds

 For address family: IPv4 Unicast
  server peer-group member
  Update group 3, subgroup 5
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

 For address family: IPv6 Unicast
  server peer-group member
  Update group 4, subgroup 6
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

  Connections established 3; dropped 2
  Last reset 02w3d01h,  No AFI/SAFI activated for peer
Local host: fe80::d277:ceff:fe4b:b47a, Local port: 179
Foreign host: fe80::5e6f:69ff:feb0:c451, Foreign port: 48256
Nexthop: 10.10.21.4
Nexthop global: fe80::d277:ceff:fe4b:b47a
Nexthop local: fe80::d277:ceff:fe4b:b47a
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 120
Read thread: on  Write thread: on  FD used: 29

BGP neighbor on Ethernet41: fe80::1623:f2ff:fecb:a9a1, remote AS 4210021027, local AS 65404, external link
Hostname: st01-comp-r01-u13
 Member of peer-group server for session parameters
  BGP version 4, remote router ID 10.10.21.27, local router ID 10.10.21.4
  BGP state = Established, up for 02w6d18h
  Last read 00:00:15, Last write 00:00:16
  Hold time is 180, keepalive interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv4 Unicast: RX advertised and received
      IPv6 Unicast: RX advertised and received
    Extended nexthop: advertised and received
      Address families by peer:
                   IPv4 Unicast
    Route refresh: advertised and received(old & new)
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: advertised and received
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: st01-sw25g-r01-u34,domain name: n/a) received (name: st01-comp-r01-u13,domain name: n/a)
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv4 Unicast, IPv6 Unicast
    End-of-RIB received: IPv4 Unicast, IPv6 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: True
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
    IPv4 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                  4          3
    Notifications:          0          4
    Updates:              272         16
    Keepalives:         34279      34279
    Route Refresh:          0          0
    Capability:             0          0
    Total:              34555      34302
  Minimum time between advertisement runs is 0 seconds

 For address family: IPv4 Unicast
  server peer-group member
  Update group 3, subgroup 5
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

 For address family: IPv6 Unicast
  server peer-group member
  Update group 4, subgroup 6
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

  Connections established 3; dropped 2
  Last reset 02w6d18h,  No AFI/SAFI activated for peer
Local host: fe80::d277:ceff:fe4b:b47a, Local port: 179
Foreign host: fe80::1623:f2ff:fecb:a9a1, Foreign port: 41992
Nexthop: 10.10.21.4
Nexthop global: fe80::d277:ceff:fe4b:b47a
Nexthop local: fe80::d277:ceff:fe4b:b47a
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 120
Read thread: on  Write thread: on  FD used: 28

BGP neighbor on Ethernet42: fe80::5e6f:69ff:feb0:c461, remote AS 4210021026, local AS 65404, external link
Hostname: st01-comp-r01-u11
 Member of peer-group server for session parameters
  BGP version 4, remote router ID 10.10.21.26, local router ID 10.10.21.4
  BGP state = Established, up for 02w6d18h
  Last read 00:00:15, Last write 00:00:16
  Hold time is 180, keepalive interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv4 Unicast: RX advertised and received
      IPv6 Unicast: RX advertised and received
    Extended nexthop: advertised and received
      Address families by peer:
                   IPv4 Unicast
    Route refresh: advertised and received(old & new)
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: advertised and received
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: st01-sw25g-r01-u34,domain name: n/a) received (name: st01-comp-r01-u11,domain name: n/a)
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv4 Unicast, IPv6 Unicast
    End-of-RIB received: IPv4 Unicast, IPv6 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: True
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
    IPv4 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                  6          3
    Notifications:          0          4
    Updates:              306         16
    Keepalives:         34279      34279
    Route Refresh:          0          0
    Capability:             0          0
    Total:              34591      34302
  Minimum time between advertisement runs is 0 seconds

 For address family: IPv4 Unicast
  server peer-group member
  Update group 3, subgroup 5
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

 For address family: IPv6 Unicast
  server peer-group member
  Update group 4, subgroup 6
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

  Connections established 3; dropped 2
  Last reset 02w6d18h,  No AFI/SAFI activated for peer
Local host: fe80::d277:ceff:fe4b:b47a, Local port: 179
Foreign host: fe80::5e6f:69ff:feb0:c461, Foreign port: 58406
Nexthop: 10.10.21.4
Nexthop global: fe80::d277:ceff:fe4b:b47a
Nexthop local: fe80::d277:ceff:fe4b:b47a
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 120
Read thread: on  Write thread: on  FD used: 38

BGP neighbor on Ethernet43: fe80::5e6f:69ff:feb0:bc81, remote AS 4210021025, local AS 65404, external link
Hostname: st01-comp-r01-u09
 Member of peer-group server for session parameters
  BGP version 4, remote router ID 10.10.21.25, local router ID 10.10.21.4
  BGP state = Established, up for 02w6d18h
  Last read 00:00:27, Last write 00:00:29
  Hold time is 180, keepalive interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv4 Unicast: RX advertised and received
      IPv6 Unicast: RX advertised and received
    Extended nexthop: advertised and received
      Address families by peer:
                   IPv4 Unicast
    Route refresh: advertised and received(old & new)
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: advertised and received
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: st01-sw25g-r01-u34,domain name: n/a) received (name: st01-comp-r01-u09,domain name: n/a)
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv4 Unicast, IPv6 Unicast
    End-of-RIB received: IPv4 Unicast, IPv6 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: True
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
    IPv4 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                  5          3
    Notifications:          0          4
    Updates:              268         20
    Keepalives:         34279      34279
    Route Refresh:          0          0
    Capability:             0          0
    Total:              34552      34306
  Minimum time between advertisement runs is 0 seconds

 For address family: IPv4 Unicast
  server peer-group member
  Update group 3, subgroup 5
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

 For address family: IPv6 Unicast
  server peer-group member
  Update group 4, subgroup 6
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

  Connections established 3; dropped 2
  Last reset 02w6d18h,  No AFI/SAFI activated for peer
Local host: fe80::d277:ceff:fe4b:b47a, Local port: 179
Foreign host: fe80::5e6f:69ff:feb0:bc81, Foreign port: 54706
Nexthop: 10.10.21.4
Nexthop global: fe80::d277:ceff:fe4b:b47a
Nexthop local: fe80::d277:ceff:fe4b:b47a
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 120
Read thread: on  Write thread: on  FD used: 30

BGP neighbor on Ethernet44: fe80::1623:f2ff:fecb:c0f1, remote AS 4210021024, local AS 65404, external link
Hostname: st01-stor-r01-u07
 Member of peer-group server for session parameters
  BGP version 4, remote router ID 10.10.21.24, local router ID 10.10.21.4
  BGP state = Established, up for 02w3d01h
  Last read 00:00:37, Last write 00:00:39
  Hold time is 180, keepalive interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv4 Unicast: RX advertised and received
      IPv6 Unicast: RX advertised and received
    Extended nexthop: advertised and received
      Address families by peer:
                   IPv4 Unicast
    Route refresh: advertised and received(old & new)
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: advertised and received
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: st01-sw25g-r01-u34,domain name: n/a) received (name: st01-stor-r01-u07,domain name: n/a)
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv4 Unicast, IPv6 Unicast
    End-of-RIB received: IPv4 Unicast, IPv6 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: True
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
    IPv4 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                  6          3
    Notifications:          0          4
    Updates:              290         12
    Keepalives:         34281      34281
    Route Refresh:          0          0
    Capability:             0          0
    Total:              34577      34300
  Minimum time between advertisement runs is 0 seconds

 For address family: IPv4 Unicast
  server peer-group member
  Update group 3, subgroup 5
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

 For address family: IPv6 Unicast
  server peer-group member
  Update group 4, subgroup 6
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

  Connections established 3; dropped 2
  Last reset 02w3d01h,  No AFI/SAFI activated for peer
Local host: fe80::d277:ceff:fe4b:b47a, Local port: 179
Foreign host: fe80::1623:f2ff:fecb:c0f1, Foreign port: 41450
Nexthop: 10.10.21.4
Nexthop global: fe80::d277:ceff:fe4b:b47a
Nexthop local: fe80::d277:ceff:fe4b:b47a
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 120
Read thread: on  Write thread: on  FD used: 32

BGP neighbor on Ethernet45: fe80::1623:f2ff:fecb:cc41, remote AS 4210021023, local AS 65404, external link
Hostname: st01-stor-r01-u05
 Member of peer-group server for session parameters
  BGP version 4, remote router ID 10.10.21.23, local router ID 10.10.21.4
  BGP state = Established, up for 02w3d01h
  Last read 00:00:00, Last write 00:00:02
  Hold time is 180, keepalive interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv4 Unicast: RX advertised and received
      IPv6 Unicast: RX advertised and received
    Extended nexthop: advertised and received
      Address families by peer:
                   IPv4 Unicast
    Route refresh: advertised and received(old & new)
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: advertised and received
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: st01-sw25g-r01-u34,domain name: n/a) received (name: st01-stor-r01-u05,domain name: n/a)
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv4 Unicast, IPv6 Unicast
    End-of-RIB received: IPv4 Unicast, IPv6 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: True
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
    IPv4 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                  5          3
    Notifications:          0          4
    Updates:              287         12
    Keepalives:         34281      34281
    Route Refresh:          0          0
    Capability:             0          0
    Total:              34573      34300
  Minimum time between advertisement runs is 0 seconds

 For address family: IPv4 Unicast
  server peer-group member
  Update group 3, subgroup 5
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

 For address family: IPv6 Unicast
  server peer-group member
  Update group 4, subgroup 6
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

  Connections established 3; dropped 2
  Last reset 02w3d01h,  No AFI/SAFI activated for peer
Local host: fe80::d277:ceff:fe4b:b47a, Local port: 179
Foreign host: fe80::1623:f2ff:fecb:cc41, Foreign port: 38224
Nexthop: 10.10.21.4
Nexthop global: fe80::d277:ceff:fe4b:b47a
Nexthop local: fe80::d277:ceff:fe4b:b47a
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 120
Read thread: on  Write thread: on  FD used: 42

BGP neighbor on Ethernet46: fe80::1623:f2ff:fecb:c0b1, remote AS 4210021022, local AS 65404, external link
Hostname: st01-stor-r01-u03
 Member of peer-group server for session parameters
  BGP version 4, remote router ID 10.10.21.22, local router ID 10.10.21.4
  BGP state = Established, up for 02w3d01h
  Last read 00:00:27, Last write 00:00:29
  Hold time is 180, keepalive interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv4 Unicast: RX advertised and received
      IPv6 Unicast: RX advertised and received
    Extended nexthop: advertised and received
      Address families by peer:
                   IPv4 Unicast
    Route refresh: advertised and received(old & new)
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: advertised and received
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: st01-sw25g-r01-u34,domain name: n/a) received (name: st01-stor-r01-u03,domain name: n/a)
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv4 Unicast, IPv6 Unicast
    End-of-RIB received: IPv4 Unicast, IPv6 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: True
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
    IPv4 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                  8          4
    Notifications:          0          6
    Updates:              331         16
    Keepalives:         34281      34281
    Route Refresh:          0          0
    Capability:             0          0
    Total:              34620      34307
  Minimum time between advertisement runs is 0 seconds

 For address family: IPv4 Unicast
  server peer-group member
  Update group 3, subgroup 5
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

 For address family: IPv6 Unicast
  server peer-group member
  Update group 4, subgroup 6
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

  Connections established 4; dropped 3
  Last reset 02w3d01h,  No AFI/SAFI activated for peer
Local host: fe80::d277:ceff:fe4b:b47a, Local port: 179
Foreign host: fe80::1623:f2ff:fecb:c0b1, Foreign port: 42602
Nexthop: 10.10.21.4
Nexthop global: fe80::d277:ceff:fe4b:b47a
Nexthop local: fe80::d277:ceff:fe4b:b47a
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 120
Read thread: on  Write thread: on  FD used: 33

BGP neighbor on Ethernet47: fe80::1623:f2ff:fecb:86e1, remote AS 4210021021, local AS 65404, external link
Hostname: st01-stor-r01-u01
 Member of peer-group server for session parameters
  BGP version 4, remote router ID 10.10.21.21, local router ID 10.10.21.4
  BGP state = Established, up for 21:19:12
  Last read 00:00:12, Last write 00:00:12
  Hold time is 180, keepalive interval is 60 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended Message: advertised and received
    AddPath:
      IPv4 Unicast: RX advertised and received
      IPv6 Unicast: RX advertised and received
    Extended nexthop: advertised and received
      Address families by peer:
                   IPv4 Unicast
    Route refresh: advertised and received(old & new)
    Enhanced Route Refresh: advertised and received
    Address Family IPv4 Unicast: advertised and received
    Address Family IPv6 Unicast: advertised and received
    Hostname Capability: advertised (name: st01-sw25g-r01-u34,domain name: n/a) received (name: st01-stor-r01-u01,domain name: n/a)
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
  Graceful restart information:
    End-of-RIB send: IPv4 Unicast, IPv6 Unicast
    End-of-RIB received: IPv4 Unicast, IPv6 Unicast
    Local GR Mode: Helper*
    Remote GR Mode: Helper
    R bit: True
    Timers:
      Configured Restart Time(sec): 120
      Received Restart Time(sec): 120
    IPv4 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
    IPv6 Unicast:
      F bit: False
      End-of-RIB sent: Yes
      End-of-RIB sent after update: No
      End-of-RIB received: Yes
      Timers:
        Configured Stale Path Time(sec): 360
  Message statistics:
    Inq depth is 0
    Outq depth is 0
                         Sent       Rcvd
    Opens:                 10          5
    Notifications:          0          8
    Updates:              367         20
    Keepalives:         34280      34280
    Route Refresh:          0          0
    Capability:             0          0
    Total:              34657      34313
  Minimum time between advertisement runs is 0 seconds

 For address family: IPv4 Unicast
  server peer-group member
  Update group 3, subgroup 5
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

 For address family: IPv6 Unicast
  server peer-group member
  Update group 4, subgroup 6
  Packet Queue length 0
  Community attribute sent to this neighbor(all)
  1 accepted prefixes

  Connections established 5; dropped 4
  Last reset 21:21:12,  No AFI/SAFI activated for peer
Local host: fe80::d277:ceff:fe4b:b47a, Local port: 179
Foreign host: fe80::1623:f2ff:fecb:86e1, Foreign port: 60568
Nexthop: 10.10.21.4
Nexthop global: fe80::d277:ceff:fe4b:b47a
Nexthop local: fe80::d277:ceff:fe4b:b47a
BGP connection: shared network
BGP Connect Retry Timer in Seconds: 120
Read thread: on  Write thread: on  FD used: 34


st01-sw25g-r01-u34# show interface
Interface Bridge is up, line protocol is down
...
Interface Ethernet0 is up, line protocol is up
  Link ups:       1    last: 2024/10/28 14:41:47.12
  Link downs:     0    last: (never)
  vrf: default
  index 13 metric 0 mtu 9100 speed 0
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
  ND advertised reachable time is 0 milliseconds
  ND advertised retransmit interval is 0 milliseconds
  ND advertised hop-count limit is 64 hops
  ND router advertisements sent: 205668 rcvd: 205678
  ND router advertisements are sent every 10 seconds
  ND router advertisements lifetime tracks ra-interval
  ND router advertisement default router preference is medium
  Hosts use stateless autoconfig for addresses.
  Neighbor address(s):
  inet6 fe80::5e6f:69ff:feb0:46f1/128
Interface Ethernet1 is up, line protocol is up
  Link ups:       2    last: 2024/11/05 11:08:55.73
  Link downs:     1    last: 2024/11/05 11:08:55.22
  vrf: default
  index 12 metric 0 mtu 9100 speed 0
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
  ND advertised reachable time is 0 milliseconds
  ND advertised retransmit interval is 0 milliseconds
  ND advertised hop-count limit is 64 hops
  ND router advertisements sent: 205673 rcvd: 205434
  ND router advertisements are sent every 10 seconds
  ND router advertisements lifetime tracks ra-interval
  ND router advertisement default router preference is medium
  Hosts use stateless autoconfig for addresses.
  Neighbor address(s):
  inet6 fe80::5e6f:69ff:feb0:4b41/128
Interface Ethernet2 is up, line protocol is up
  Link ups:       2    last: 2024/11/20 14:35:40.03
  Link downs:     1    last: 2024/11/20 14:34:44.58
  vrf: default
  index 14 metric 0 mtu 9100 speed 0
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
  ND advertised reachable time is 0 milliseconds
  ND advertised retransmit interval is 0 milliseconds
  ND advertised hop-count limit is 64 hops
  ND router advertisements sent: 205666 rcvd: 205666
  ND router advertisements are sent every 10 seconds
  ND router advertisements lifetime tracks ra-interval
  ND router advertisement default router preference is medium
  Hosts use stateless autoconfig for addresses.
  Neighbor address(s):
  inet6 fe80::5e6f:69ff:feb0:4b61/128
Interface Ethernet3 is down
..
Interface Ethernet4 is up, line protocol is up
  Link ups:       0    last: (never)
  Link downs:     0    last: (never)
  vrf: default
  index 17 metric 0 mtu 9100 speed 0
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
  ND advertised reachable time is 0 milliseconds
  ND advertised retransmit interval is 0 milliseconds
  ND advertised hop-count limit is 64 hops
  ND router advertisements sent: 205678 rcvd: 205685
  ND router advertisements are sent every 10 seconds
  ND router advertisements lifetime tracks ra-interval
  ND router advertisement default router preference is medium
  Hosts use stateless autoconfig for addresses.
  Neighbor address(s):
  inet6 fe80::1623:f3ff:fef5:6101/128
Interface Ethernet5 is up, line protocol is up
  Link ups:       3    last: 2024/10/28 14:48:39.54
  Link downs:     2    last: 2024/10/28 14:47:32.57
  vrf: default
  index 11 metric 0 mtu 9100 speed 0
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
  ND advertised reachable time is 0 milliseconds
  ND advertised retransmit interval is 0 milliseconds
  ND advertised hop-count limit is 64 hops
  ND router advertisements sent: 205657 rcvd: 205631
  ND router advertisements are sent every 10 seconds
  ND router advertisements lifetime tracks ra-interval
  ND router advertisement default router preference is medium
  Hosts use stateless autoconfig for addresses.
  Neighbor address(s):
  inet6 fe80::5e6f:69ff:feb0:49c1/128
Interface Ethernet6 is down
...
Interface Ethernet32 is up, line protocol is up
  Link ups:       1    last: 2024/10/28 14:41:28.30
  Link downs:     0    last: (never)
  vrf: default
  index 40 metric 0 mtu 9100 speed 0
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
Interface Ethernet33 is up, line protocol is up
  Link ups:       1    last: 2024/10/28 14:41:22.20
  Link downs:     0    last: (never)
  vrf: default
  index 44 metric 0 mtu 9100 speed 0
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
Interface Ethernet34 is up, line protocol is up
  Link ups:       1    last: 2024/10/28 14:41:24.23
  Link downs:     0    last: (never)
  vrf: default
  index 43 metric 0 mtu 9100 speed 0
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
Interface Ethernet35 is up, line protocol is up
  Link ups:       1    last: 2024/10/28 14:41:26.77
  Link downs:     0    last: (never)
  vrf: default
  index 45 metric 0 mtu 9100 speed 0
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
Interface Ethernet36 is up, line protocol is up
  Link ups:       1    last: 2024/10/28 14:41:34.40
  Link downs:     0    last: (never)
  vrf: default
  index 48 metric 0 mtu 9100 speed 0
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
Interface Ethernet37 is up, line protocol is up
  Link ups:       1    last: 2024/10/28 14:41:27.79
  Link downs:     0    last: (never)
  vrf: default
  index 49 metric 0 mtu 9100 speed 0
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
Interface Ethernet38 is up, line protocol is up
  Link ups:       1    last: 2024/10/28 14:40:13.78
  Link downs:     0    last: (never)
  vrf: default
  index 50 metric 0 mtu 9100 speed 0
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
  ND advertised reachable time is 0 milliseconds
  ND advertised retransmit interval is 0 milliseconds
  ND advertised hop-count limit is 64 hops
  ND router advertisements sent: 205678 rcvd: 205674
  ND router advertisements are sent every 10 seconds
  ND router advertisements lifetime tracks ra-interval
  ND router advertisement default router preference is medium
  Hosts use stateless autoconfig for addresses.
  Neighbor address(s):
  inet6 fe80::5e6f:69ff:feb0:c0f1/128
Interface Ethernet39 is up, line protocol is up
  Link ups:       1    last: 2024/10/28 14:40:11.00
  Link downs:     0    last: (never)
  vrf: default
  index 51 metric 0 mtu 9100 speed 0
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
  ND advertised reachable time is 0 milliseconds
  ND advertised retransmit interval is 0 milliseconds
  ND advertised hop-count limit is 64 hops
  ND router advertisements sent: 205678 rcvd: 205675
  ND router advertisements are sent every 10 seconds
  ND router advertisements lifetime tracks ra-interval
  ND router advertisement default router preference is medium
  Hosts use stateless autoconfig for addresses.
  Neighbor address(s):
  inet6 fe80::1623:f2ff:fecb:b381/128
Interface Ethernet40 is up, line protocol is up
  Link ups:       1    last: 2024/10/28 14:40:18.38
  Link downs:     0    last: (never)
  vrf: default
  index 52 metric 0 mtu 9100 speed 0
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
  ND advertised reachable time is 0 milliseconds
  ND advertised retransmit interval is 0 milliseconds
  ND advertised hop-count limit is 64 hops
  ND router advertisements sent: 205677 rcvd: 205676
  ND router advertisements are sent every 10 seconds
  ND router advertisements lifetime tracks ra-interval
  ND router advertisement default router preference is medium
  Hosts use stateless autoconfig for addresses.
  Neighbor address(s):
  inet6 fe80::5e6f:69ff:feb0:c451/128
Interface Ethernet41 is up, line protocol is up
  Link ups:       1    last: 2024/10/28 14:41:52.47
  Link downs:     0    last: (never)
  vrf: default
  index 47 metric 0 mtu 9100 speed 0
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
  ND advertised reachable time is 0 milliseconds
  ND advertised retransmit interval is 0 milliseconds
  ND advertised hop-count limit is 64 hops
  ND router advertisements sent: 205668 rcvd: 205665
  ND router advertisements are sent every 10 seconds
  ND router advertisements lifetime tracks ra-interval
  ND router advertisement default router preference is medium
  Hosts use stateless autoconfig for addresses.
  Neighbor address(s):
  inet6 fe80::1623:f2ff:fecb:a9a1/128
Interface Ethernet42 is up, line protocol is up
  Link ups:       1    last: 2024/10/28 14:41:59.38
  Link downs:     0    last: (never)
  vrf: default
  index 54 metric 0 mtu 9100 speed 0
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
  ND advertised reachable time is 0 milliseconds
  ND advertised retransmit interval is 0 milliseconds
  ND advertised hop-count limit is 64 hops
  ND router advertisements sent: 205668 rcvd: 205666
  ND router advertisements are sent every 10 seconds
  ND router advertisements lifetime tracks ra-interval
  ND router advertisement default router preference is medium
  Hosts use stateless autoconfig for addresses.
  Neighbor address(s):
  inet6 fe80::5e6f:69ff:feb0:c461/128
Interface Ethernet43 is up, line protocol is up
  Link ups:       1    last: 2024/10/28 14:42:03.74
  Link downs:     0    last: (never)
  vrf: default
  index 55 metric 0 mtu 9100 speed 0
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
  ND advertised reachable time is 0 milliseconds
  ND advertised retransmit interval is 0 milliseconds
  ND advertised hop-count limit is 64 hops
  ND router advertisements sent: 205667 rcvd: 205667
  ND router advertisements are sent every 10 seconds
  ND router advertisements lifetime tracks ra-interval
  ND router advertisement default router preference is medium
  Hosts use stateless autoconfig for addresses.
  Neighbor address(s):
  inet6 fe80::5e6f:69ff:feb0:bc81/128
Interface Ethernet44 is up, line protocol is up
  Link ups:       1    last: 2024/10/28 14:41:55.28
  Link downs:     0    last: (never)
  vrf: default
  index 53 metric 0 mtu 9100 speed 0
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
  ND advertised reachable time is 0 milliseconds
  ND advertised retransmit interval is 0 milliseconds
  ND advertised hop-count limit is 64 hops
  ND router advertisements sent: 205668 rcvd: 205667
  ND router advertisements are sent every 10 seconds
  ND router advertisements lifetime tracks ra-interval
  ND router advertisement default router preference is medium
  Hosts use stateless autoconfig for addresses.
  Neighbor address(s):
  inet6 fe80::1623:f2ff:fecb:c0f1/128
Interface Ethernet45 is up, line protocol is up
  Link ups:       1    last: 2024/10/28 14:42:00.92
  Link downs:     0    last: (never)
  vrf: default
  index 59 metric 0 mtu 9100 speed 0
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
  ND advertised reachable time is 0 milliseconds
  ND advertised retransmit interval is 0 milliseconds
  ND advertised hop-count limit is 64 hops
  ND router advertisements sent: 205667 rcvd: 205668
  ND router advertisements are sent every 10 seconds
  ND router advertisements lifetime tracks ra-interval
  ND router advertisement default router preference is medium
  Hosts use stateless autoconfig for addresses.
  Neighbor address(s):
  inet6 fe80::1623:f2ff:fecb:cc41/128
Interface Ethernet46 is up, line protocol is up
  Link ups:       1    last: 2024/10/28 14:42:04.00
  Link downs:     0    last: (never)
  vrf: default
  index 60 metric 0 mtu 9100 speed 0
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
  ND advertised reachable time is 0 milliseconds
  ND advertised retransmit interval is 0 milliseconds
  ND advertised hop-count limit is 64 hops
  ND router advertisements sent: 205667 rcvd: 205670
  ND router advertisements are sent every 10 seconds
  ND router advertisements lifetime tracks ra-interval
  ND router advertisement default router preference is medium
  Hosts use stateless autoconfig for addresses.
  Neighbor address(s):
  inet6 fe80::1623:f2ff:fecb:c0b1/128
Interface Ethernet47 is up, line protocol is up
  Link ups:       2    last: 2024/11/20 12:38:24.29
  Link downs:     1    last: 2024/11/20 12:37:25.99
  vrf: default
  index 58 metric 0 mtu 9100 speed 0
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
  ND advertised reachable time is 0 milliseconds
  ND advertised retransmit interval is 0 milliseconds
  ND advertised hop-count limit is 64 hops
  ND router advertisements sent: 205665 rcvd: 205665
  ND router advertisements are sent every 10 seconds
  ND router advertisements lifetime tracks ra-interval
  ND router advertisement default router preference is medium
  Hosts use stateless autoconfig for addresses.
  Neighbor address(s):
  inet6 fe80::1623:f2ff:fecb:86e1/128
Interface Ethernet48 is down
...
Interface Ethernet72 is up, line protocol is up
  Link ups:       0    last: (never)
  Link downs:     0    last: (never)
  vrf: default
  index 68 metric 0 mtu 9100 speed 0
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
  ND advertised reachable time is 0 milliseconds
  ND advertised retransmit interval is 0 milliseconds
  ND advertised hop-count limit is 64 hops
  ND router advertisements sent: 205678 rcvd: 205678
  ND router advertisements are sent every 10 seconds
  ND router advertisements lifetime tracks ra-interval
  ND router advertisement default router preference is medium
  Hosts use stateless autoconfig for addresses.
  Neighbor address(s):
  inet6 fe80::922d:77ff:fe58:2650/128
Interface Ethernet76 is up, line protocol is up
  Link ups:       1    last: 2024/10/28 14:40:13.02
  Link downs:     0    last: (never)
  vrf: default
  index 69 metric 0 mtu 9100 speed 0
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
  ND advertised reachable time is 0 milliseconds
  ND advertised retransmit interval is 0 milliseconds
  ND advertised hop-count limit is 64 hops
  ND router advertisements sent: 205677 rcvd: 205677
  ND router advertisements are sent every 10 seconds
  ND router advertisements lifetime tracks ra-interval
  ND router advertisement default router preference is medium
  Hosts use stateless autoconfig for addresses.
  Neighbor address(s):
  inet6 fe80::922d:77ff:fe58:2750/128
Interface Loopback0 is up, line protocol is up
  Link ups:       0    last: (never)
  Link downs:     0    last: (never)
  vrf: default
  index 63 metric 0 mtu 65536 speed 0
  flags: <UP,BROADCAST,RUNNING,NOARP>
  Type: Ethernet
  HWaddr: 4a:87:58:6d:3e:cf
  inet 10.10.21.4/32 unnumbered
  inet6 fd0c:cc24:75a0:1:10:10:21:4/128
  inet6 fe80::4887:58ff:fe6d:3ecf/64
  Interface Type Other
  Interface Slave Type None
  protodown: off
Interface bcm0 is down
...
Interface docker0 is up, line protocol is down
...
Interface dummy is down
...
Interface eth1 is down
...
Interface lo is up, line protocol is up
  Link ups:       0    last: (never)
  Link downs:     0    last: (never)
  vrf: default
  index 1 metric 0 mtu 65536 speed 0
  flags: <UP,LOOPBACK,RUNNING>
  Type: Loopback
  Interface Type Other
  Interface Slave Type None
  protodown: off
Interface pimreg is up, line protocol is up
  Link ups:       1    last: 2024/10/28 14:40:10.18
  Link downs:     0    last: (never)
  vrf: default
  index 70 metric 0 mtu 1472 speed 0
  flags: <UP,RUNNING,NOARP>
  Type: PIMSM registration
  Interface Type Other
  Interface Slave Type None
  protodown: off
Interface pimreg5000 is down
...
Interface eth0 is up, line protocol is up
  Link ups:       1    last: 2023/11/29 17:20:00.02
  Link downs:     2    last: 2023/11/29 17:20:00.02
  vrf: mgmt
  index 2 metric 0 mtu 1500 speed 1000
  flags: <UP,BROADCAST,RUNNING,MULTICAST>
  Type: Ethernet
  HWaddr: d0:77:ce:4b:b4:7a
  inet 10.10.23.107/24
  inet6 fe80::d277:ceff:fe4b:b47a/64
  Interface Type Other
  Interface Slave Type Vrf
  protodown: off
Interface lo-m is up, line protocol is up
  Link ups:       1    last: 2023/11/29 17:20:00.05
  Link downs:     0    last: (never)
  vrf: mgmt
  index 73 metric 0 mtu 1500 speed 0
  flags: <UP,BROADCAST,RUNNING,NOARP>
  Type: Ethernet
  HWaddr: da:e2:c2:ae:30:2f
  inet6 fe80::d8e2:c2ff:feae:302f/64
  Interface Type Other
  Interface Slave Type Vrf
  protodown: off
Interface mgmt is up, line protocol is up
  Link ups:       1    last: 2023/11/29 17:19:59.94
  Link downs:     0    last: (never)
  vrf: mgmt
  index 72 metric 0 mtu 65575 speed 0
  flags: <UP,RUNNING,NOARP>
  Type: Ethernet
  HWaddr: aa:e0:85:9e:aa:ea
  Interface Type VRF
  Interface Slave Type None
  protodown: off

```


