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

As a consequence, this means that BGP routers with private ASN numbers are active on all systems involved
(e.g. servers and switches) in the cloud setup and these exchange information with each other via the network topology.

As a result, redundant paths of a server system, for example, are no longer managed via (multi-chassis) LACP,
but the respective server or switch has topology information that allows it to route traffic efficiently or deal with availability problems.

The detailes of this concept are heavily releated to the [great network documentation](https://docs.metal-stack.io/stable/overview/networking/) of 
Metal-Stack. Furthermore, the present design is strongly inspired by the work of Dinesh G. Dutt on 
BGP ([bgp-ebook](https://www.nvidia.com/en-us/networking/border-gateway-protocol/)) and the 
work ‘[Cloud Native Data Centre Networking](https://www.oreilly.com/library/view/cloud-native-data/9781492045595/)’ (O'Reilly) 
published in 2019, which provides various interesting basics.

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
