# Hostname Naming Scheme

The followings section describes how to name systems.
The procedure is primarily intended for larger installations.
Nevertheless, we have chosen this approach so that we do not have to adapt the host names when creating documentation, for example.

## Goals

The goal of the nameing scheme are:

- `Identification and Classification:` The naming standard allows for clear identification and classification of different roles of hardware components in the datacenter.
  The naming convention specifies the role or function of the hardware, such as network switches, jump nodes, management hosts, cluster controller nodes, compute nodes, and storage nodes.
- `Location Information:` The naming convention provides information about the physical location of the hardware within the datacenter.
  The information is helpful for efficient management, maintenance, and troubleshooting.
- `Ease of Maintenance:` The naming standard facilitates ease of maintenance by providing a systematic way to identify and locate hardware components.
- `Scalability:` The naming standard is scalable, allowing for the addition of more hardware components without sacrificing clarity.
- `Quick Reference:` The naming convention provides a quick reference for understanding the role, location, and orientation
  of a hardware component within the datacenter. This is particularly useful in large-scale and complex datacenter environments.

## Details of the naming standard

The naming scheme looks like that:

```
<datacenter>-<role>-r<rack>-u<rack-location>
<datacenter>-<role>-r<rack>-u<rack-location>-s<system-nr>
```

The elements of the nameing scheme:

* `datacenter`
  * A short identifier for the datacenter
  * I our case always: st01
  * Should not contain dashes
* `role`
  * `sw<speed>g` : Network switches
    * Network switch hardware
    * The speed of the majority of ports, if equal take the faster
      (i.e: sw100, sw25g, sw10g, sw1g, ...)
  * `gw` : Jumpnode
    Gateway to access the cloud environment. Provides external access by SSH, VPN
    Provides access to the internet for specific purposes.
  * `mgmt`: Management host
    Management workload for maintaining the lifecycle of the cloud system.
    Can be stopped temporarily without directly affecting the availibility of the cloud environment itself.
  * `ctl` : Cluster controller node
    Manages a cluster of machines - i.e ceph osd nodes
  * `comp` : Compute node with or without storage services (hyperconverged)
    Runs workload deployed on the cloud system (virtualization, containers, workload, ...).
  * `stor` : Storage Node
  * `tst` : Test Node
* `rack`
  * identifier of the datacenter rack
  * fixed length of two digits
* `rack-location`:
  * the lower unit location of the hardware in the rack
  * fixed number of digits (two or more, padded with leading zeros)
  * renamed when moving the hardware to another location (cattle vs. pets)
* `system-nr`:
  * used for the case if a chassis contains more than one system
  * typically a single digit, counted from top left to bottom right

## Examples

  * `st01-mgmt-r13-3031`
    A managment node in Stödelen Rack 13 deployed at rack unit 30,31
  * `st01-sw-r13-u30`
    A switch in Stödelen Rack 13 on deployed at rack unit 31
  * `st01-stor-r13-u10`
    A storage node in Stödelen Rack 13 deployed at rack unit 10,11,12,13
  * `st01-comp-r13-u10-s4`
    A the 4th and last compute node in Stödelen Rack 13 deployed at rack unit 10,11,12,13
    (deployed on bottom right)
