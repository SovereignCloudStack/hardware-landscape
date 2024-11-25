# Networks

## General

Domain naming scheme: `<hostname>.<net>.landscape.scs.community`.

## Defined networks

With the exception of the networks marked with Uplink “Yes”, no host in the listed networks
has direct access to the Internet. Services that are deployed on the manager hosts must be used for DNS, NTP, HTTP and HTTPS.

| Networkname  | Network           | Router         | V(x)Lan   | Description                                 | Uplink |
|--------------|-------------------|----------------|-----------|---------------------------------------------|--------|
| vpn1         | 10.10.1.0/24      | 10.10.2.1      | -         | VPN transfer/client network                 |        |
| zone1-public | 10.80.0.0/20      | 10.80.0.1      | VXLAN 80  | Provider LAN                                | Yes    |
| zone1        | 10.10.21.0/24     | 10.10.21.1     | -         | Production Node Network                     |        |
| mgmt-p2p     | 10.10.22.0/24     | 10.10.22.1     | -         | Out of band for rack level                  |        |
| mgmt         | 10.10.23.0/24     | 10.10.23.1     | VLAN 23   | Out of band access for switches and servers |        |
| lab          | 10.10.24.0/24     | 10.10.24.1     | VLAN 24   | Lab Node Network                            |        |
| datacenter   | 192.168.104.40/29 | 192.168.104.41 | -         | Internet Uplink Datacenter                  | Yes    |
| mgmt-docker  | 172.16.0.0/12     |                | -         | Network used for Docker containers in mgmt  | Yes    |

To provide connections, two auxiliary scripts are integrated which ensure that access is configured, filtered and translated (NAT).

* Dynamic addition of NFTables rules: [/etc/networkd-dispatcher/routable.d/scs_add_nftables_rules.sh](https://github.com/SovereignCloudStack/hardware-landscape/blob/main/environments/custom/roles/scs-landscape-nodes/files/scripts/scs_add_nftables_rules.sh)
* Add remote parners for the VXLan80 bridge [/etc/networkd-dispatcher/routable.d/scs_configure_vxlan.sh](https://github.com/SovereignCloudStack/hardware-landscape/blob/main/environments/custom/roles/scs-landscape-nodes/templates/scs_configure_vxlan.sh.j2)

## Reserved Address Ranges

The following list describes all dynamic address ranges.
The containing ips are not statically assigned to a particular host.

| Networkname   | From                | To               | Description                                               |
|---------------|---------------------|------------------|-----------------------------------------------------------|
| mgmt          | 10.10.23.5          | 10.10.23.9       | DHCP range for hardware deployments                       |
| prod1         | 10.10.21.200        | 10.10.21.201     | Openstack API Endpoints                                   |
| prod1         | 10.10.21.202        |                  | Controller Kubernetes, Static                             |
| prod1         | 10.10.21.203        | 10.10.21.220     | Kubernetes Loadbalancer IPs, Dynamic                      |
| prod1         | 10.10.21.221        | 10.10.21.250     | Loadbalancer URLs for Openstack, Dynamic                  |
| datacenter    | 192.168.104.42      | 192.168.104.43   | IPs for Basition Host Uplinks                             |


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

