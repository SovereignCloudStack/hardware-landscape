# Networks

## General

Domain naming scheme: `<hostname>.<net>.landscape.scs.community`.

## Defined networks

With the exception of the networks marked with Uplink “Yes”, no host in the listed networks
has direct access to the Internet. Services that are deployed on the manager hosts must be used for DNS, NTP, HTTP and HTTPS.

| Networkname  | Network                   | Router     | V(x)Lan  | Description                                 | Uplink |
| ------------ | ------------------------- | ---------- | -------- | ------------------------------------------- | ------ |
| vpn1         | 10.10.1.0/24              | 10.10.2.1  | -        | VPN transfer/client network                 |        |
| zone1-public | 10.80.0.0/20              | 10.80.0.1  | VXLAN 80 | Provider LAN                                | Yes    |
| zone1        | 10.10.21.0/24             | 10.10.21.1 | -        | Production Node Network                     |        |
| mgmt-p2p     | 10.10.22.0/24             | 10.10.22.1 | -        | Out of band for rack level                  |        |
| mgmt         | 10.10.23.0/24             | 10.10.23.1 | VLAN 23  | Out of band access for switches and servers |        |
| lab          | 10.10.24.0/24             | 10.10.24.1 | VLAN 24  | Lab Node Network                            |        |
| datacenter   | 10.202.0.0/24             | 10.202.0.1 | -        | Internet Uplink Datacenter                  | Yes    |
| datacenter   | 2a00:12e8:701:1e:ec4::/64 | SLAAC      | -        | Internet Uplink Datacenter (IPv6)           | Yes    |
| mgmt-docker  | 172.16.0.0/12             |            | -        | Network used for Docker containers in mgmt  | Yes    |

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
| datacenter    | 10.202.0.4          | 10.202.0.254     | IPs for Basition Host Uplinks                             |


## Port Forwarding Access


### st01-mgmt-r01-u30

* MAC: 0c:c4:7a:fe:e6:6d
* Firewall IP (NAT):
  * IP: 45.139.159.237 (BINAT -> 10.202.0.30)
* Internal interface
  * Interface: eno2 (Remote OSBA-DL-S7-L)
  * Internal IP: 10.202.0.30
  * Subnet: 255.255.255.0 (/24)
  * Gateway: 10.202.0.1
  * IPv6: 2a00:12e8:701:1e:ec4:7aff:fefe:e66d
  * DNS: 85.158.4.230, 93.92.134.126
  * Ports:
   * SSH: 22/TCP from 0.0.0.0/0 + ::/0
   * Wireguard: 51820/UDP from 0.0.0.0/0 + ::/0

### st01-mgmt-r01-u31

* MAC: 0c:c4:7a:fe:e6:75
* Firewall IP (NAT):
  * IP: 45.139.159.238 (BINAT -> 10.202.0.31)
* Internal interface
  * Interface: eno2 (Remote Temp-Downlink-S…)
  * Internal IP: 10.202.0.31
  * Subnet: 255.255.255.0 (/24)
  * Gateway: 10.202.0.1
  * IPv6: 2a00:12e8:701:1e:ec4:7aff:fefe:e675
  * DNS: 85.158.4.230, 93.92.134.126
  * Ports:
   * SSH: 22/TCP from 0.0.0.0/0 + ::/0
   * Wireguard: 51820/UDP from 0.0.0.0/0 + ::/0
