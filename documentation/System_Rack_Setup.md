# Rack Setup


| POS | #U |    System Name        |      Type      | Hardwaretype                                                        | Environment | Comments                         |
|-----|----|-----------------------|----------------|---------------------------------------------------------------------|-------------|----------------------------------|
| TOP | -  |                       |                |                                                                     |             |                                  |
| 47  | 1  | st01-sw1g-r01-u47     | SW JH          |                                                                     | Datacenter  | MGMT-Access for Lab              |
| 46  | 1  | st01-gw-r01-u46       | Jumpnode JH    |                                                                     | Datacenter  | Router, Jumphost, Serial Access  |
| 45  | 1  |                       | Testnode       |                                                                     | Lab         | planned, 2x1GBE, 2x25GBE         |
| 44  | 1  |                       | Testnode       |                                                                     | Lab         | planned, 2x1GBE, 2x25GBE         |
| 43  | 1  |                       | Testnode       |                                                                     | Lab         | planned, 2x1GBE, 2x25GBE         |
| 42  | 1  | st01-sw1g-r01-u42     | SW LAB 1G      | [Edgecore 4630-54TE-O-AC-B](./network/Edgecore_4630-54TE-O-AC-B.md) | Lab         |                                  |
| 41  | 1  | st01-sw100g-r01-u41   | SW LAB 100G    | [Edgecore 7726-32X-O-AC-B](./network/Edgecore_7726-32X-O-AC-B.md)   | Lab         |                                  |
| 40  | 1  | st01-sw25g-r01-u40    | SW LAB 25G     | [Edgecore 7326-56X-O-AC-B](./network/Edgecore_7326-56X-O-AC-B.md)   | Lab         |                                  |
| 39  | 1  | st01-sw10g-r01-u39    | SW LAB 10G     | [Edgecore 5835-54X-O-AC-B](./network/Edgecore_5835-54X-O-AC-B.md)   | Lab         |                                  |
| 38  | 1  | st01-sw10g-r01-u38    | SW LAB 10G     | [Edgecore 5835-54X-O-AC-B](./network/Edgecore_5835-54X-O-AC-B.md)   | Lab         |                                  |
| 37  | 1  | st01-sw100g-r01-u37   | SW SPINE       | [Edgecore 7726-32X-O-AC-B](./network/Edgecore_7726-32X-O-AC-B.md)   | Prod        |                                  |
| 36  | 1  | st01-sw100g-r01-u36   | SW SPINE       | [Edgecore 7726-32X-O-AC-B](./network/Edgecore_7726-32X-O-AC-B.md)   | Prod        |                                  |
| 35  | 1  | st01-sw25g-r01-u35    | SW LEAF        | [Edgecore 7326-56X-O-AC-B](./network/Edgecore_7326-56X-O-AC-B.md)   | Prod        |                                  |
| 34  | 1  | st01-sw25g-r01-u34    | SW LEAF        | [Edgecore 7326-56X-O-AC-B](./network/Edgecore_7326-56X-O-AC-B.md)   | Prod        |                                  |
| 33  | 1  | st01-sw1g-r01-u33     | SW MGMT        | [Edgecore 4630-54TE-O-AC-B](./network/Edgecore_4630-54TE-O-AC-B.md) | Prod        |                                  |
| 32  | 1  | st01-sw1g-r01-u32     | SW MGMT        | [Edgecore 4630-54TE-O-AC-B](./network/Edgecore_4630-54TE-O-AC-B.md) | Prod        |                                  |
| 31  | 1  | st01-mgmt-r01-u31     | Manager        | [Supermicro A2SDV-4C-LN8F](./servers/Supermicro_A2SDV-4C-LN8F.md)   | Prod        | OSISM Manager Node               |
| 30  | 1  | st01-mgmt-r01-u30     | Manager        | [Supermicro A2SDV-4C-LN8F](./servers/Supermicro_A2SDV-4C-LN8F.md)   | Prod        | Observability                    |
| 29  | 1  | st01-ctl-r01-u29      | Controller     | [Supermicro A2SDV-8C-LN8F](./servers/Supermicro_A2SDV-8C-LN8F.md)   | Prod        | Openstack Controller,Ceph Mon,.. |
| 28  | 1  | st01-ctl-r01-u28      | Controller     | [Supermicro A2SDV-8C-LN8F](./servers/Supermicro_A2SDV-8C-LN8F.md)   | Prod        | Openstack Controller,Ceph Mon,.. |
| 27  | 1  | st01-ctl-r01-u27      | Controller     | [Supermicro A2SDV-8C-LN8F](./servers/Supermicro_A2SDV-8C-LN8F.md)   | Prod        | Openstack Controller,Ceph Mon,.. |
| 26  | 1  | st01-comp-r01-u26     | Compute ARM    | [Supermicro ARS-110M-NR](./servers/Supermicro_ARS-110M-NR.md)       | Prod        |                                  |
| 25  | 1  | st01-comp-r01-u25     | Compute ARM    | [Supermicro ARS-110M-NR](./servers/Supermicro_ARS-110M-NR.md)       | Prod        |                                  |
| 24  | 1  | st01-comp-r01-u24     | Compute ARM    | [Supermicro ARS-110M-NR](./servers/Supermicro_ARS-110M-NR.md)       | Prod        |                                  |
| 23  | 1  | st01-comp-r01-u23     | Compute ARM    | [Supermicro ARS-110M-NR](./servers/Supermicro_ARS-110M-NR.md)       | Prod        |                                  |
| 22  | 1  | st01-comp-r01-u22     | Compute ARM    | [Supermicro ARS-110M-NR](./servers/Supermicro_ARS-110M-NR.md)       | Prod        |                                  |
| 21  | 1  | st01-comp-r01-u21     | Compute ARM    | [Supermicro ARS-110M-NR](./servers/Supermicro_ARS-110M-NR.md)       | Prod        |                                  |
| 19  | 2  | st01-comp-r01-u19     | Compute Intel  | [Supermicro H12SSL-NT](./servers/Supermicro_H12SSL-NT.md)           | Prod        |                                  |
| 17  | 2  | st01-comp-r01-u17     | Compute Intel  | [Supermicro H12SSL-NT](./servers/Supermicro_H12SSL-NT.md)           | Prod        |                                  |
| 15  | 2  | st01-comp-r01-u15     | Compute Intel  | [Supermicro H12SSL-NT](./servers/Supermicro_H12SSL-NT.md)           | Prod        |                                  |
| 13  | 2  | st01-comp-r01-u13     | Compute Intel  | [Supermicro H12SSL-NT](./servers/Supermicro_H12SSL-NT.md)           | Prod        |                                  |
| 11  | 2  | st01-comp-r01-u11     | Compute Intel  | [Supermicro H12SSL-NT](./servers/Supermicro_H12SSL-NT.md)           | Prod        |                                  |
| 9   | 2  | st01-comp-r01-u09     | Compute Intel  | [Supermicro H12SSL-NT](./servers/Supermicro_H12SSL-NT.md)           | Prod        |                                  |
| 7   | 2  | st01-stor-r01-u07     | Storage        | [Supermicro H12SSL-CT](./servers/Supermicro_H12SSL-CT.md)           | Prod        |                                  |
| 5   | 2  | st01-stor-r01-u05     | Storage        | [Supermicro H12SSL-CT](./servers/Supermicro_H12SSL-CT.md)           | Prod        |                                  |
| 3   | 2  | st01-stor-r01-u03     | Storage        | [Supermicro H12SSL-CT](./servers/Supermicro_H12SSL-CT.md)           | Prod        |                                  |
| 1   | 2  | st01-stor-r01-u01     | Storage        | [Supermicro H12SSL-CT](./servers/Supermicro_H12SSL-CT.md)           | Prod        |                                  |
| BT  | -  |                       |                |                                                                     |             |                                  |
