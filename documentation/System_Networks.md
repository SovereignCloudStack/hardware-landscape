# Networks

## General

Domain nameing scheme: <net>.landscape.sovereignit.de

## Defined networks

| Networkname   | Network             | Router           | VLan    | Description                                     |
|---------------|---------------------|------------------|---------|-------------------------------------------------|
| vpn1          | 10.10.1.0/24        | 10.10.2.1        | -       | VPN transfer/client network                     |
| mgmt          | 10.10.23.0/24       | 10.10.23.1       | 23      | Out of band access for switches and servers     |
| lab           | 10.10.24.0/24       | 10.10.24.1       | 24      | Lab Node Network                                |
| prod1         | 10.25.0.0/22        | 10.25.0.1        | 25      | Production Node Network                         |
| prod1-stor    | 10.26.0.0/22        | 10.26.0.1        | 26      | Production Storage Network                      |


## Port Forwarding Access

### st01-gw-r01-u46

* DHCP: yes
* Interface: enp9s0
* IP: 192.168.104.42
* External Connection:
  * IP: 153.92.93.119
  * Ports:
   * SSH: 41115
   * Wireguard: 51820
* Interface: enp9s0 (Remote Temp-Downlink-S…)
* Subnet: 255.255.255.248 (/29)
* Gateway: 192.168.104.41
* DNS: 192.168.104.41

### st01-mgmt-r01-u30

* DHCP: No
* External Connection:
  * IP: 188.244.104.28
  * Ports:
   * SSH: 22
   * Wireguard: 51820
* Interface: eno2 (Remote OSBA-DL-S7-L)
* IP: 192.168.104.43
* Subnet: 255.255.255.248 (/29)
* Gateway: 192.168.104.41
* DNS: 192.168.104.41

```
ip addr add 192.168.104.43/29 dev eno2
ip link set eno2 up
ip route add default via 192.168.104.41 dev eno2
```
