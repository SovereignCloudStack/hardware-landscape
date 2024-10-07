# SONiC GNS3 testbed deployment and configuration

This tutorial walks you through setting up and configuring a basic testbed environment in the GNS3 simulation platform.
The setup includes three SONiC switches (Spine, Leaf1, Leaf2) with community images and two PCs connected to Leaf1 and Leaf2.

The guide also covers a basic BGP L3 underlay configuration using FRR.

![GNS3_basic.png](images/GNS3_basic.png)

## SONiC GNS3 testbed portable project

If you prefer to bypass the configuration steps detailed below, you can simplify the process by importing the SONiC GNS3
portable project. Download it from the following [URL](https://api.gx-scs.sovereignit.cloud:8080/swift/v1/AUTH_602778bad3d3470cbe58c4f7611e8eb7/vp04/gns3/SONiC_testbed_202311_601084.gns3project) and 
skip directly to the [Validate the testbed](#validate-the-testbed) section.

Disclaimer: Please note that the GNS3 portable project URL is anticipated to become unavailable in the coming months. We appreciate your understanding.

To walk through the configuration, follow the steps outlined below.

## Prerequisites

* GNS3
  * Select the installer for your favourite OS: https://www.gns3.com/software/download
* SONiC GNS3 appliance
  * Follow instructions [here](../general.md#gns3-simulation-environment)
  * The tutorial is intended to use SONiC community images. It was tested with community image SONiC-202311-601084

## SONiC GNS3 testbed configuration

* Drag and drop the SONiC switches and PCs, and wire them as shown in the architecture diagram
* Remove arbitrary config defaults 
  * The SONiC community image includes a default configuration that enables various ports and assigns arbitrary IP addresses
    to them. Replace this configuration with another default setting that avoids arbitrary configurations.
    For this purpose, we can use a predefined config template:
    ```bash
    sudo su -
    sonic-cfggen  -H --preset l3 -k Force10-S6000 > /etc/sonic/config_db.json
    config reload -y
    ```
* Modify the metadata configuration in `/etc/sonic/config_db.json` on each SONiC device
  * Ensure `"docker_routing_config_mode": "split-unified"` is set so that the FRR configuration is not generated from ConfigDB,
    and a single FRR config file is used
  * Ensure each SONiC switch has a unique hostname and mac address
  ```json
  "DEVICE_METADATA": {
    "localhost": {
      "buffer_model": "traditional",
      "default_bgp_status": "up",
      "default_pfcwd_status": "disable",
      "docker_routing_config_mode": "split-unified",
      "hostname": "spine",
      "hwsku": "Force10-S6000",
      "mac": "0c:2e:02:80:00:00",
      ...
    }
  }
  ```
  * Reload the SONiC configuration by running `config reload -y` after making changes
* Configure switch interfaces, e.g. via SONiC CLI as follows
  * Spine
  ```bash
  sudo config interface ip add Ethernet0 1.1.1.1/31
  sudo config interface ip add Ethernet4 1.1.1.2/31  # interface ID 1
  ```
  * Leaf1
  ```bash
  sudo config interface ip add Ethernet0 1.1.1.0/31
  sudo config interface ip add Ethernet32 192.168.100.1/24  # interface ID 8
  ```
  * Leaf1
  ```bash
  sudo config interface ip add Ethernet4 1.1.1.3/31  # interface ID 1
  sudo config interface ip add Ethernet32 192.168.200.1/24  # interface ID 8
  ```
  * Save the interfaces configuration by running `config save -y` after making changes
* Configure FRR BGP
  * Find the FRR config files `configs/leaf1_frr.conf`, `configs/leaf2_frr.conf`, `configs/spine_frr.conf`, and apply them as follows:
  ```bash
  sudo cp <sonic-sw>_frr.conf /etc/sonic/frr/frr.conf
  sudo chown 300:300 /etc/sonic/frr/frr.conf
  docker restart bgp
  ```
* Configure PC1 and PC2
  * Configure PC's IP address and proper gateway
  ```text
  PC1> ip 192.168.100.100/24 192.168.100.1
  PC2> ip 192.168.200.100/24 192.168.200.1
  ```

## Validate the testbed

* If you simply import the SONiC GNS3 portable project into your GNS3 instance, wait a few seconds for all switches to boot up
* Validate the interfaces' setup
  * Connect to, for example, the Spine switch console (the default credential for login is admin/YourPaSsWoRd) and verify
    the interfaces IP configuration and status
  ```yaml
  $ show ip int
  Interface    Master    IPv4 address/mask    Admin/Oper    BGP Neighbor    Neighbor IP
  -----------  --------  -------------------  ------------  --------------  -------------
  Ethernet0              1.1.1.1/31           up/up         N/A             N/A
  Ethernet4              1.1.1.2/31           up/up         N/A             N/A
  Loopback0              192.168.0.2/32       up/up         N/A             N/A
  docker0                240.127.1.1/24       up/down       N/A             N/A
  lo                     127.0.0.1/16         up/up         N/A             N/A
  ```
  * Validate whether you see UP/UP state of connected interfaces via e.g. `$ show int status`
  * Explore interfaces configuration via `show runningconfiguration interfaces` or via `sudo cat /etc/sonic/config_db.json`
* Validate the BGP configuration
  * Connect to, for example, the Spine switch and verify the routes propagated by the BGP protocol
  ```bash
  $ show ip route
  Codes: K - kernel route, C - connected, S - static, R - RIP,
         O - OSPF, I - IS-IS, B - BGP, E - EIGRP, N - NHRP,
         T - Table, v - VNC, V - VNC-Direct, A - Babel, D - SHARP,
         F - PBR, f - OpenFabric,
         > - selected route, * - FIB route, q - queued route, r - rejected route
  
  C>*1.1.1.0/31 is directly connected, Ethernet0, 00:02:02
  C>*1.1.1.2/31 is directly connected, Ethernet4, 00:02:02
  B>*192.168.0.1/32 [20/0] via 1.1.1.0, Ethernet0, 00:01:53
  C>*192.168.0.2/32 is directly connected, Loopback0, 00:02:02
  B>*192.168.0.3/32 [20/0] via 1.1.1.3, Ethernet4, 00:01:53
  B>*192.168.100.0/24 [20/0] via 1.1.1.0, Ethernet0, 00:01:53
  B>*192.168.200.0/24 [20/0] via 1.1.1.3, Ethernet4, 00:01:53
  ```
  * Explore BGP configuration via `show runningconfiguration bgp` or via `sudo cat /etc/sonic/frr/frr.conf`
* Open console of the PC1 or PC2 and try to `ping` the whole infrastructure
  * SONiC switches should be reachable e.g. via its Loopback IPs and PC1 via 192.168.100.100 and PC2 via IP 192.168.200.100
