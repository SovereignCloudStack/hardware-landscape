# System Network Wireing

**WORK IN PROGRESS**

The following standard describes how particular system components are wired in general within hosting racks.

# General aspects

* every system gets a out of band access with a single ethernet connection
* inter-switch connections are always wired in a symetric way with the same ports
  in order from the bottom of the rack to the top on all involved switches
* Systems are plugged to the particalur switches in order from the bottom
  of the rack to the top on all involved switches


# Documentation

Description of the fields:

* Source: The source system hostname
* SPort: The Ethernet Port used on the source system
* Destination: The source system hostname
* DPort: The Ethernet Port used on the destination system
* Linktype: The type of the hardware link
* Connection Group: A handle which describes the common nature of the connection
  (VLAN, Portchannel, ...)
* IdentGroup: A handle which describes the combination or the common criteria of the links

Rules:
* Connections should not be documented redundantly
* Add a description of the used "Connection Groups"
* Add a description of the used "IdentGroup"


# Example:

## Connection Groups:

* UPSTREAM2
  * Tagged VLAN 23, "mgmt"
  * Tagged VLAN 25, "prod1"
  * Tagged VLAN 26, "prod1-stor"
* OOB-MGMT
  * Un-Tagged VLAN 23, "mgmt"
* SPINE-LEAF
  * Tagged VLAN 25, "prod1"
  * Tagged VLAN 26, "prod1-stor"

## IdentGroup:

* PC1:
  * Portchannel between the Spine Switches
  * Tagged VLAN 25, "prod1"
  * Tagged VLAN 26, "prod1-stor"


## Port List:

| Source               | SPort         | Destination         | DPort         | Linktype     | Connection Group | IdentGroup | Description                      |
|----------------------|---------------|---------------------|---------------|--------------|------------------|------------|----------------------------------|
| st01-sw1g-r01-u32    | eth0          | st01-sw1g-r01-u47   | Ethernet1     | RJ45/1GBE    | UPSTREAM2        |            |                                  |
| st01-sw1g-r01-u32    | Ethernet0     | st01-sw1g-r01-u47   | Ethernet3     | RJ45/1GBE    | OOB-MGMT         |            |                                  |
| st01-sw1g-r01-u32    | Ethernet1     | st01-comp-r01-u21   | MGMT          | RJ45/1GBE    | OOB-MGMT         |            |                                  |
| st01-sw1g-r01-u32    | Ethernet2     | st01-comp-r01-u23   | MGMT          | RJ45/1GBE    | OOB-MGMT         |            |                                  |
| st01-sw1g-r01-u32    | Ethernet3     | st01-comp-r01-u25   | MGMT          | RJ45/1GBE    | OOB-MGMT         |            |                                  |
| st01-sw1g-r01-u32    | Ethernet35    | st01-mgmt-r01-u31   | MGMT          | RJ45/1GBE    | OOB-MGMT         |            |                                  |
| st01-sw1g-r01-u32    | Ethernet36    | st01-ctl-r01-u29    | MGMT          | RJ45/1GBE    | OOB-MGMT         |            |                                  |
| st01-sw1g-r01-u32    | Ethernet36    | st01-ctl-r01-u29    | MGMT          | RJ45/1GBE    | OOB-MGMT         |            |                                  |
| st01-sw25g-r01-u36   | Ethernet120   | st01-sw100g-r01-u37 | Ethernet120   | QSFP28/100G  | SPINE-SPINE      | PC1        | DEACTIVATED                      |
| st01-sw25g-r01-u36   | Ethernet124   | st01-sw100g-r01-u37 | Ethernet124   | QSFP28/100G  | SPINE-SPINE      | PC1        | DEACTIVATED                      |
| st01-sw25g-r01-u36   | Portchannel01 | st01-sw100g-r01-u37 | Portchannel01 | QSFP28/100G  | SPINE-SPINE      | PC1        | DEACTIVATED                      |

