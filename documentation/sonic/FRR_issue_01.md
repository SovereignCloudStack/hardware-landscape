# Test whether the FRR route map option [set src ADDRESS](https://docs.frrouting.org/en/stable-7.1/zebra.html#clicmd-setsrcADDRESS) is mandatory for BGP configuration

TL;DR: BGP routing works without route-map set src option, but the router is not able to reach remote addresses due to missing source IP address in local routes.

If the set src ADDRESS option is removed from the working BGP config:
```bash
vtysh
conf t
no route-map RM_SET_SRC6 permit 10
no route-map RM_SET_SRC permit 10
no ip protocol bgp route-map RM_SET_SRC
no ipv6 protocol bgp route-map RM_SET_SRC6
```
Then the local router routes do not contain source IP address to reach the remote networks (discovered by BGP):
```bash
$ show ip route 
Codes: K - kernel route, C - connected, S - static, R - RIP,
       O - OSPF, I - IS-IS, B - BGP, E - EIGRP, N - NHRP,
       T - Table, v - VNC, V - VNC-Direct, A - Babel, D - SHARP,
       F - PBR, f - OpenFabric,
       > - selected route, * - FIB route, q - queued route, r - rejected route

C>*10.10.21.4/32 is directly connected, Loopback0, 01:17:05
B>*10.10.21.5/32 [20/0] via fe80::e53:8aff:fefe:2, Ethernet32, 01:14:07
C>*192.168.100.0/24 is directly connected, Ethernet28, 00:43:05
B>*192.168.200.0/24 [20/0] via fe80::e53:8aff:fefe:2, Ethernet32, 00:38:33
---
$ ip route 
10.10.21.5 via 169.254.0.1 dev Ethernet32 proto bgp metric 20 onlink  # route does not contain SRC IP, as a result of above setting
192.168.100.0/24 dev Ethernet28 proto kernel scope link src 192.168.100.1 # directly connected network, it has SRC IP
192.168.200.0/24 via 169.254.0.1 dev Ethernet32 proto bgp metric 20 onlink # route does not contain SRC IP, as a result of above setting
240.127.1.0/24 dev docker0 proto kernel scope link src 240.127.1.1 linkdown 

```
The above `ip route` command shows two BGP discovered prefixes `10.10.21.5` and `192.168.200.0/24` that does not contain SRC IP.
As a result "ping" from router to address like 10.10.21.5 does not work.

This in not optimal but test shows that BGP routing works as expected when the device lives in 192.168.100.0/24 network
wants to reach the device lives in 192.168.200.0/24 network. 

It means that the missing `route map set src ADDRESS` option affects local router routes. 

See also [#14195](https://github.com/sonic-net/sonic-buildimage/issues/14195)
