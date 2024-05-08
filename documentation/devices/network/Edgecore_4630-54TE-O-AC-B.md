
# Overview

* Model: Edgecore 4630-54TE-O-AC-B
* Feature overview:
  * 48 RJ45 GbE Ports
  * 4 x 25G SFP28
  * 2 x 100G QSFP28
  * OS: [Sonic Community](https://sonicfoundation.dev/)
* References
  * [Vendor Information](https://www.edge-core.com/productsInfo.php?cls=1&cls2=9&cls3=587&id=927)
  * [Specification](https://www.edge-core.com/productsInfo.php?cls=1&cls2=9&cls3=587&id=927) : [2023-026-EPS201_AS4630-54TE_DS_R04_20230308.pdf](https://github.com/SCS-Private/orga-infra/blob/main/scs-system-landscape/spec_sheets/network//2023-026-EPS201_AS4630-54TE_DS_R04_20230308.pdf)
* Application purpose / description:
  * Mgmt

# Hardware Overview

| Name                | Serial Number   | OS-Flavor  | Delivery date | Management IPs/VXLANs | MGMT MAC          | Serial      | Comments                        |
|---------------------|-----------------|------------|---------------|-----------------------|-------------------|-------------|---------------------------------|
| st01-sw1g-r01-u33   | 463054TE2315074 | Enterprise | 2023-10-12    | 10.10.23.100          | d0:77:ce:2b:31:c4 | AMBOb113318 | sw01, production, mgmt          |
| st01-sw1g-r01-u32   | 463054TE2315088 | Enterprise | 2023-10-12    | 10.10.23.101          | d0:77:ce:2b:3f:c4 | DXBOb113318 | sw02, Production, mgmt          |
| st01-sw1g-r01-u47   | 463054TE2315093 | Enterprise | 2023-10-12    | 10.10.23.102          | d0:77:ce:2b:44:c4 | EFBGb113318 | sw03, datacenter, not final     |
| st01-sw1g-r01-u42   | 463054TE2315114 | Enterprise | 2023-10-12    | 10.10.23.103          | d0:77:ce:2b:59:c4 | EGBGb113318 | lab, mgmt                       |

