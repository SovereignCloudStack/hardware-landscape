# Networks

## General

Domain naming scheme: `<hostname>.<net>.landscape.scs.community`.

## Defined networks

| Networkname   | Network             | Router           | VLan    | Description                                     |
|---------------|---------------------|------------------|---------|-------------------------------------------------|
| vpn1          | 10.10.1.0/24        | 10.10.2.1        | -       | VPN transfer/client network                     |
| zone1         | 10.10.21.0/24       | 10.10.21.1       | -       | Production Node Network                         |
| mgmt-p2p      | 10.10.22.0/24       | 10.10.22.1       | -       | Out of band for rack level                      |
| mgmt          | 10.10.23.0/24       | 10.10.23.1       | 23      | Out of band access for switches and servers     |
| lab           | 10.10.24.0/24       | 10.10.24.1       | 24      | Lab Node Network                                |

## Reserved Adress Ranges

The following list describes all dynamic adress ranges.
The containing ips are not statically assigned to a particular host.

| Networkname   | From                | To               | Description                                               |
|---------------|---------------------|------------------|-----------------------------------------------------------|
| mgmt          | 10.10.23.5          | 10.10.23.9       | DHCP range for hardware deployments                       |
| prod1         | 10.10.21.200        | 10.10.21.201     | Openstack API Endpoints                                   |
| prod1         | 10.10.21.202        |                  | Controller Kubernetes, Static                             |
| prod1         | 10.10.21.203        | 10.10.21.220     | Kubernetes Loadbalancer IPs, Dynamic                      |
| prod1         | 10.10.21.221        | 10.10.21.250     | Loadbalancer URLs for Openstack, Dynamic                  |


## Port Forwarding Access


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
sed -i "~s,nameserver.*$,nameserver 8.8.8.8," /etc/resolv.conf
```

### st01-mgmt-r01-u31

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

