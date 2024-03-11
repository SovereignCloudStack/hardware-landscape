# Documentation of the network links

## Connection Groups:

* UPSTREAM1
  * Tagged VLAN 23, "mgmt"
  * Tagged VLAN 24, "lab"
  * Tagged VLAN 25, "prod1"
  * Tagged VLAN 26, "prod1-stor"
* UPSTREAM2
  * Tagged VLAN 23, "mgmt"
  * Tagged VLAN 25, "prod1"
  * Tagged VLAN 26, "prod1-stor"
* UPSTREAM3
  * Tagged VLAN 23, "mgmt"
  * Tagged VLAN 24, "lab"
* LAB
  * Tagged VLAN 24, "lab"
  * Tagged VLAN 23, "mgmt"
* SPINE-UPSTREAM2
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


## Connection Documentation

| Source               | SPort         | Destination         | DPort         | Linktype     | Connection Group | IdentGroup | Description                      |
|----------------------|---------------|---------------------|---------------|--------------|------------------|------------|----------------------------------|
| st01-sw1g-r01-u47    | eth0          | st01-mgmt-r01-u30   | TODO          | RJ45/1GBE    | OOB-MGMT         |            |                                  |
| st01-sw1g-r01-u47    | Ethernet0     | st01-gw-r01-u46     | enp1s0        | RJ45/1GBE    | UPSTREAM1        |            |                                  |
| st01-sw1g-r01-u47    | Ethernet1     | st01-sw1g-r01-u32   | eth0          | RJ45/1GBE    | OOB-MGMT         |            |                                  |
| st01-sw1g-r01-u47    | Ethernet3     | st01-sw1g-r01-u32   | Ethernet0     | RJ45/1GBE    | SPINE-UPSTREAM2  |            |                                  |
| st01-sw1g-r01-u47    | Ethernet4     | st01-sw1g-r01-u33   | eth0          | RJ45/1GBE    | OOB-MGMT         |            |                                  |
| st01-sw1g-r01-u47    | Ethernet5     | st01-sw1g-r01-u33   | Ethernet0     | RJ45/1GBE    | SPINE-UPSTREAM2  |            |                                  |

| Source               | SPort         | Destination         | DPort         | Linktype     | Connection Group | IdentGroup | Description                      |
|----------------------|---------------|---------------------|---------------|--------------|------------------|------------|----------------------------------|
| st01-sw1g-r01-u32    | eth0          | st01-sw1g-r01-u47   | Ethernet1     | RJ45/1GBE    | UPSTREAM2        |            |                                  |
| st01-sw1g-r01-u32    | Ethernet0     | st01-sw1g-r01-u47   | Ethernet3     | RJ45/1GBE    | OOB-MGMT         |            |                                  |
| st01-sw1g-r01-u32    | Ethernet1     | st01-comp-r01-u21   | MGMT          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u32    | Ethernet2     | st01-comp-r01-u23   | MGMT          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u32    | Ethernet3     | st01-comp-r01-u25   | MGMT          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u32    | Ethernet35    | st01-mgmt-r01-u31   | MGMT          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u32    | Ethernet36    | st01-ctl-r01-u29    | MGMT          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u32    | Ethernet37    | st01-ctl-r01-u27    | MGMT          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u32    | Ethernet41    | st01-comp-r01-u17   | MGMT          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u32    | Ethernet42    | st01-comp-r01-u13   | MGMT          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u32    | Ethernet43    | st01-comp-r01-u09   | MGMT          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u32    | Ethernet44    | st01-stor-r01-u05   | MGMT          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u32    | Ethernet45    | st01-stor-r01-u01   | MGMT          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u32    | Ethernet46    | st01-sw100g-r01-u36 | eth0          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u32    | Ethernet47    | st01-sw25g-r01-u34  | eth0          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u32    | Ethernet52    | st01-sw100g-r01-u37 | Ethernet108   | QSFP28/100G  | SPINE-UPSTREAM2  |            | DEACTIVATED                      |
| st01-sw1g-r01-u32    | Ethernet56    | st01-sw100g-r01-u36 | Ethernet108   | QSFP28/100G  | SPINE-UPSTREAM2  |            |                                  |

Activate/deactivate cross-links:
```
sudo config interface shutdown Ethernet52
sudo config interface startup Ethernet52
```


| Source               | SPort         | Destination         | DPort         | Linktype     | Connection Group | IdentGroup | Description                      |
|----------------------|---------------|---------------------|---------------|--------------|------------------|------------|----------------------------------|
| st01-sw1g-r01-u33    | eth0          | st01-sw1g-r01-u47   | Ethernet4     | RJ45/1GBE    | UPSTREAM2        |            |                                  |
| st01-sw1g-r01-u33    | Ethernet0     | st01-sw1g-r01-u47   | Ethernet5     | RJ45/1GBE    | OOB-MGMT         |            |                                  |
| st01-sw1g-r01-u33    | Ethernet1     | st01-comp-r01-u22   | MGMT          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u33    | Ethernet2     | st01-comp-r01-u24   | MGMT          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u33    | Ethernet3     | st01-comp-r01-u26   | MGMT          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u33    | Ethernet36    | st01-ctl-r01-u28    | MGMT          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u33    | Ethernet37    | st01-mgmt-r01-u30   | MGMT          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u33    | Ethernet41    | st01-comp-r01-u19   | MGMT          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u33    | Ethernet42    | st01-comp-r01-u15   | MGMT          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u33    | Ethernet43    | st01-comp-r01-u11   | MGMT          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u33    | Ethernet44    | st01-stor-r01-u07   | MGMT          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u33    | Ethernet45    | st01-stor-r01-u03   | MGMT          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u33    | Ethernet46    | st01-sw100g-r01-u37 | eth0          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u33    | Ethernet47    | st01-sw25g-r01-u35  | eth0          | RJ45/1GBE    | OOB-MGMT         |            | TODO, OOB PROD SERVER            |
| st01-sw1g-r01-u33    | Ethernet52    | st01-sw100g-r01-u36 | Ethernet108   | QSFP28/100G  | SPINE-UPSTREAM2  |            | DEACTIVATED                      |
| st01-sw1g-r01-u33    | Ethernet56    | st01-sw100g-r01-u37 | Ethernet108   | QSFP28/100G  | SPINE-UPSTREAM2  |            |                                  |

Activate/deactivate cross-links:
```
sudo config interface shutdown Ethernet52
sudo config interface startup Ethernet52
```


| Source               | SPort         | Destination         | DPort         | Linktype     | Connection Group | IdentGroup | Description                      |
|----------------------|---------------|---------------------|---------------|--------------|------------------|------------|----------------------------------|
| st01-sw25g-r01-u36   | eth0          | st01-sw1g-r01-u32   | Ethernet46    | RJ45/1GBE    | OOB-MGMT         |            |                                  |
| st01-sw25g-r01-u36   | Ethernet104   | st01-sw1g-r01-u33   | Ethernet52    | QSFP28/100G  | SPINE-LEAF       |            | DEACTIVATED                      |
| st01-sw25g-r01-u36   | Ethernet108   | st01-sw1g-r01-u32   | Ethernet56    | QSFP28/100G  | SPINE-UPSTREAM2  |            |                                  |
| st01-sw25g-r01-u36   | Ethernet112   | st01-sw25g-r01-u35  | Ethernet72    | QSFP28/100G  | SPINE-UPSTREAM2  |            | DEACTIVATED                      |
| st01-sw25g-r01-u36   | Ethernet116   | st01-sw25g-r01-u34  | Ethernet76    | QSFP28/100G  | SPINE-LEAF       |            |                                  |
| st01-sw25g-r01-u36   | Ethernet120   | st01-sw100g-r01-u37 | Ethernet120   | QSFP28/100G  | SPINE-SPINE      | PC1        | DEACTIVATED                      |
| st01-sw25g-r01-u36   | Ethernet124   | st01-sw100g-r01-u37 | Ethernet124   | QSFP28/100G  | SPINE-SPINE      | PC1        | DEACTIVATED                      |
| st01-sw25g-r01-u36   | Portchannel01 | st01-sw100g-r01-u37 | Portchannel01 | QSFP28/100G  | SPINE-SPINE      | PC1        | DEACTIVATED                      |


Activate/deactivate cross-links:
```
sudo config interface shutdown Ethernet120,Ethernet124,Portchannel01,Ethernet104,Ethernet112
sudo config interface startup Ethernet120,Ethernet124,Portchannel01,Ethernet104,Ethernet112
```


| Source               | SPort         | Destination         | DPort         | Linktype     | Connection Group | IdentGroup | Description                      |
|----------------------|---------------|---------------------|---------------|--------------|------------------|------------|----------------------------------|
| st01-sw100g-r01-u37  | eth0          | st01-sw1g-r01-u33   | Ethernet46    | RJ45/1GBE    | OOB-MGMT         |            |                                  |
| st01-sw100g-r01-u37  | Ethernet104   | st01-sw1g-r01-u32   | Ethernet52    | QSFP28/100G  | SPINE-LEAF       |            | DEACTIVATED                      |
| st01-sw100g-r01-u37  | Ethernet108   | st01-sw1g-r01-u33   | Ethernet56    | QSFP28/100G  | SPINE-UPSTREAM2  |            |                                  |
| st01-sw100g-r01-u37  | Ethernet112   | st01-sw25g-r01-u34  | Ethernet72    | QSFP28/100G  | SPINE-UPSTREAM2  |            | DEACTIVATED                      |
| st01-sw100g-r01-u37  | Ethernet116   | st01-sw25g-r01-u35  | Ethernet76    | QSFP28/100G  | SPINE-LEAF       |            |                                  |
| st01-sw100g-r01-u37  | Ethernet120   | st01-sw100g-r01-u36 | Ethernet120   | QSFP28/100G  | SPINE-SPINE      | PC1        | DEACTIVATED                      |
| st01-sw100g-r01-u37  | Ethernet124   | st01-sw100g-r01-u36 | Ethernet120   | QSFP28/100G  | SPINE-SPINE      | PC1        | DEACTIVATED                      |
| st01-sw100g-r01-u37  | Portchannel01 | st01-sw100g-r01-u36 | Portchannel01 | QSFP28/100G  | SPINE-SPINE      | PC1        | DEACTIVATED                      |

Activate/deactivate cross-links:
```
sudo config interface shutdown Ethernet120,Ethernet124,Portchannel01,Ethernet104,Ethernet112
sudo config interface startup Ethernet120,Ethernet124,Portchannel01,Ethernet104,Ethernet112
```


| Source               | SPort         | Destination         | DPort         | Linktype     | Connection Group | IdentGroup | Description                      |
|----------------------|---------------|---------------------|---------------|--------------|------------------|------------|----------------------------------|
| st01-sw25g-r01-u34   | eth0          | st01-sw1g-r01-u32   | Ethernet47    | RJ45/1GBE    | OOB-MGMT         |            |                                  |
| st01-sw25g-r01-u34   | Ethernet5     | st01-mgmt-r01-u30   | eth0???       | SFP+/25G     | OOB-MGMT (later UPSTREAM1)        |            | TODO: Add real interface name    |
| st01-sw25g-r01-u34   | Ethernet72    | st01-sw100g-r01-u37 | Ethernet112   | QSFP28/100G  | SPINE-LEAF       |            |                                  |
| st01-sw25g-r01-u34   | Ethernet76    | st01-sw100g-r01-u36 | Ethernet116   | QSFP28/100G  | SPINE-LEAF       |            |                                  |

Activate/deactivate cross-links:
```
sudo config interface shutdown Ethernet72
sudo config interface startup  Ethernet72
```



| Source               | SPort         | Destination         | DPort         | Linktype     | Connection Group | IdentGroup | Description                      |
|----------------------|---------------|---------------------|---------------|--------------|------------------|------------|----------------------------------|
| st01-sw25g-r01-u35   | eth0          | st01-sw1g-r01-u32   | Ethernet47    | RJ45/1GBE    | OOB-MGMT         |            |                                  |
| st01-sw25g-r01-u35   | Ethernet5     | st01-mgmt-r01-u30   | eth1???       | SFP+/25G     | OOB-MGMT (later UPSTREAM1)        |            | TODO: Add real interface name    |
| st01-sw25g-r01-u35   | Ethernet72    | st01-sw100g-r01-u36 | Ethernet112   | QSFP28/100G  | SPINE-LEAF       |            |                                  |
| st01-sw25g-r01-u35   | Ethernet76    | st01-sw100g-r01-u37 | Ethernet116   | QSFP28/100G  | SPINE-LEAF       |            |                                  |

```
sudo config interface shutdown Ethernet72
sudo config interface startup  Ethernet72
```

| Source               | SPort         | Destination         | DPort         | Linktype     | Connection Group | IdentGroup | Description                      |
|----------------------|---------------|---------------------|---------------|--------------|------------------|------------|----------------------------------|
| st01-sw1g-r01-u42    | eth0          | st01-sw1g-r01-u47   | Ethernet2     | RJ45/1GBE    | OOB-MGMT         |            |                                  |
| st01-sw1g-r01-u42    | Ethernet0     | st01-sw1g-r01-u47   | Ethernet8     | RJ45/1GBE    | UPSTREAM3        |            |                                  |
| st01-sw1g-r01-u42    | Ethernet52    | st01-sw100g-r01-u41 | Ethernet96    | QSFP28/100G  | LAB              | PC2        |                                  |
| st01-sw1g-r01-u42    | Ethernet56    | st01-sw100g-r01-u41 | Ethernet100   | QSFP28/100G  | LAB              | PC2        |                                  |
| st01-sw1g-r01-u42    | PortChannel02 | st01-sw100g-r01-u41 | PortChannel02 | QSFP28/100G  | LAB              | PC2        |                                  |

```
sudo config interface shutdown Ethernet52,Ethernet56,PortChannel02
sudo config interface startup Ethernet52,Ethernet56,PortChannel02
```

# TODO: Not yet completly configured

| Source               | SPort         | Destination         | DPort         | Linktype     | Connection Group | IdentGroup | Description                      |
|----------------------|---------------|---------------------|---------------|--------------|------------------|------------|----------------------------------|
| st01-sw100g-r01-u41  | eth0          | st01-sw1g-r01-u47   | Ethernet46    | RJ45/1GBE    | OOB-MGMT         |            |                                  |
| st01-sw100g-r01-u41  | Ethernet96    | st01-sw1g-r01-u42   | Ethernet56    | QSFP28/100G  | LAB              | PC2        | i                                 |
| st01-sw100g-r01-u41  | Ethernet100   | st01-sw1g-r01-u42   | Ethernet56    | QSFP28/100G  | LAB              | PC2        |                                  |
| st01-sw100g-r01-u41  | Ethernet112   | st01-sw10g-r01-u39  | Ethernet64    | QSFP28/100G  | LAB              | PC4        |                                  |
| st01-sw100g-r01-u41  | Ethernet116   | st01-sw10g-r01-u39  | Ethernet60    | QSFP28/100G  | LAB              | PC4        |                                  |
| st01-sw100g-r01-u41  | Ethernet120   | st01-sw10g-r01-u38  | Ethernet60    | QSFP28/100G  | LAB              | PC5        |                                  |
| st01-sw100g-r01-u41  | Ethernet124   | st01-sw10g-r01-u38  | Ethernet64    | QSFP28/100G  | LAB              | PC5        |                                  |

```
sudo config vlan member del 24 PortChannel01
sudo config portchannel member del PortChannel01 Ethernet96
sudo config portchannel member del PortChannel01 Ethernet100
sudo config portchannel del PortChannel01

sudo config portchannel add PortChannel05
sudo config portchannel member add PortChannel05 Ethernet120
sudo config portchannel member add PortChannel05 Ethernet124
sudo config vlan member add 24 PortChannel05
show interfaces status PortChannel04

sudo config portchannel add PortChannel05
sudo config portchannel member add PortChannel05 Ethernet120
sudo config portchannel member add PortChannel05 Ethernet124
sudo config vlan member add 24 PortChannel05
show interfaces status PortChannel04
```


| Source               | SPort         | Destination         | DPort         | Linktype     | Connection Group | IdentGroup | Description                      |
|----------------------|---------------|---------------------|---------------|--------------|------------------|------------|----------------------------------|
| st01-sw25g-r01-u40   |               |                     |               |              |                  |            |                                  |

| Source               | SPort         | Destination         | DPort         | Linktype     | Connection Group | IdentGroup | Description                      |
|----------------------|---------------|---------------------|---------------|--------------|------------------|------------|----------------------------------|
| st01-sw10g-r01-u39   |               |                     |               |              |                  |            |                                  |

| Source               | SPort         | Destination         | DPort         | Linktype     | Connection Group | IdentGroup | Description                      |
|----------------------|---------------|---------------------|---------------|--------------|------------------|------------|----------------------------------|
| st01-sw10g-r01-u38   |               |                     |               |              |                  |            |                                  |
|----------------------|---------------|---------------------|---------------|--------------|------------------|------------|----------------------------------|


## TODO

```
show interfaces status|awk '/"Oper Speed/{print $0} $9 ~ "up" && $8 == "up" {print $0;count++}END{print "\n" count " links"}'
lldpshow
show vlan brief
config vlan member add 23 Interface0

```

| Source               | SPort         | Destination         | DPort         | Linktype     | Connection Group | IdentGroup | Description                      |
|----------------------|---------------|---------------------|---------------|--------------|------------------|------------|----------------------------------|
| st01-sw100g-r01-u41  | eth0          | st01-sw1g-r01-u47   | Ethernet46    | RJ45/1GBE    | OOB-MGMT         |            |                                  |
| st01-sw100g-r01-u41  | Ethernet96    | st01-sw1g-r01-u42   | Ethernet56    | QSFP28/100G  | LAB              | PC2        |                                  |
| st01-sw100g-r01-u41  | Ethernet100   | st01-sw1g-r01-u42   | Ethernet56    | QSFP28/100G  | LAB              | PC2        |                                  |
| st01-sw100g-r01-u41  | Ethernet112   | st01-sw10g-r01-u39  | Ethernet64    | QSFP28/100G  | LAB              | PC4        |                                  |
| st01-sw100g-r01-u41  | Ethernet116   | st01-sw10g-r01-u39  | Ethernet60    | QSFP28/100G  | LAB              | PC4        |                                  |
| st01-sw100g-r01-u41  | Ethernet120   | st01-sw10g-r01-u38  | Ethernet60    | QSFP28/100G  | LAB              | PC5        |                                  |
| st01-sw100g-r01-u41  | Ethernet124   | st01-sw10g-r01-u38  | Ethernet64    | QSFP28/100G  | LAB              | PC5        |                                  |
|----------------------|---------------|---------------------|---------------|--------------|------------------|------------|----------------------------------|
| st01-sw25g-r01-u40   |               |                     |               |              |                  |            |                                  |
|----------------------|---------------|---------------------|---------------|--------------|------------------|------------|----------------------------------|
| st01-sw10g-r01-u39   |               |                     |               |              |                  |            |                                  |
|----------------------|---------------|---------------------|---------------|--------------|------------------|------------|----------------------------------|
| st01-sw10g-r01-u38   |               |                     |               |              |                  |            |                                  |
|----------------------|---------------|---------------------|---------------|--------------|------------------|------------|----------------------------------|

| st01-comp-r01-u09    |               |                     |               |              |                  |            |                                  |
| st01-comp-r01-u11    |               |                     |               |              |                  |            |                                  |
| st01-comp-r01-u13    |               |                     |               |              |                  |            |                                  |
| st01-comp-r01-u15    |               |                     |               |              |                  |            |                                  |
| st01-comp-r01-u17    |               |                     |               |              |                  |            |                                  |
| st01-comp-r01-u19    |               |                     |               |              |                  |            |                                  |
| st01-comp-r01-u21    |               |                     |               |              |                  |            |                                  |
| st01-comp-r01-u22    |               |                     |               |              |                  |            |                                  |
| st01-comp-r01-u23    |               |                     |               |              |                  |            |                                  |
| st01-comp-r01-u24    |               |                     |               |              |                  |            |                                  |
| st01-comp-r01-u25    |               |                     |               |              |                  |            |                                  |
| st01-comp-r01-u26    |               |                     |               |              |                  |            |                                  |
| st01-ctl-r01-u27     |               |                     |               |              |                  |            |                                  |
| st01-ctl-r01-u28     |               |                     |               |              |                  |            |                                  |
| st01-ctl-r01-u29     |               |                     |               |              |                  |            |                                  |
| st01-mgmt-r01-u30    |               |                     |               |              |                  |            |                                  |
| st01-mgmt-r01-u31    |               |                     |               |              |                  |            |                                  |
| st01-stor-r01-u01    |               |                     |               |              |                  |            |                                  |
| st01-stor-r01-u03    |               |                     |               |              |                  |            |                                  |
| st01-stor-r01-u07    |               |                     |               |              |                  |            |                                  |
