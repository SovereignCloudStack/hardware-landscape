
# Overview

* Model: Supermicro ARS-110M-NR
* Feature overview:
  * ARM
  * Single-CPU mind. 64-Core (Physical Cores)
  * two 1+ Gbps
  * four 25 Gbps SFP+ Netzwerkschnittstellen,
  * 512 GB ECC RAM
  * three 3,2 TB NVMe
  * two 480 GB SSD/NVMe
  * Disk enterprise-version, DPWD >= 3.0
  * 1 HE
  * Multiple management interfaces
    (interfaces have a range of macs from column "MGMT MAC" to "Comments")
  * Needs the purchase of a [management licence](https://store.supermicro.com/out-of-band-sft-oob-lic.html?utm=newsm)
* Versions
  * BMC: OpenBMC 51.02.13.00
  * BIOS: 2.10
* References
  * System
    * [System Information](https://www.supermicro.com/de/products/system/megadc/1u/ars-110m-nr)
    * Specification: [ars-110m-nr.pdf](https://github.com/SCS-Private/orga-infra/blob/main/scs-system-landscape/spec_sheets/servers//ars-110m-nr.pdf)
  * Motherboard:
    * [Motherboard](https://www.supermicro.com/de/products/motherboard/R12SPD-A)
  * Chassis:
    * [Vendor Information](https://www.supermicro.com/de/products/chassis/2u/la26/scla26e1c4-r609lp)
    * Specification [SCLA26.pdf](https://github.com/SCS-Private/orga-infra/blob/main/scs-system-landscape/spec_sheets/servers//SCLA26.pdf)
  * Licence Data: [orga-infra/ .. /supermicro-bmc-licences/<mac-adress>.txt](https://github.com/SCS-Private/orga-infra/tree/main/scs-system-landscape/supermicro-bmc-licences/)
* Application purpose / description:
  * Openstack compute servers

# Hardware Overview


| Name                      | Serial Number   | Delivery date | Management IP  | ☰                        | MGMT MAC          | Comments                        |
|---------------------------|-----------------|---------------|----------------|--------------------------|-------------------|---------------------------------|
| st01-comp-r01-u21         | 240073-BTO      | 2024-01-26    | 10.10.23.15    | [☰](https://10.10.23.15) | 7c:c2:55:86:36:6d | up to mac "7c:c2:55:86:36:6f"    |
| st01-comp-r01-u22         | 240072-BTO      | 2024-01-26    | 10.10.23.16    | [☰](https://10.10.23.16) | 7c:c2:55:86:38:80 | up to mac "7c:c2:55:86:38:82"    |
| st01-comp-r01-u23         | 240071-BTO      | 2024-01-26    | 10.10.23.17    | [☰](https://10.10.23.17) | 7c:c2:55:81:4a:86 | label does not provide that     |
| st01-comp-r01-u24         | 240070-BTO      | 2024-01-26    | 10.10.23.18    | [☰](https://10.10.23.18) | 7c:c2:55:86:36:cd | up to mac "7c:c2:55:86:36:cf"    |
| st01-comp-r01-u25         | 240069-BTO      | 2024-01-26    | 10.10.23.19    | [☰](https://10.10.23.19) | 7c:c2:55:86:36:c4 | up to mac "7c:c2:55:86:36:c6"    |
| st01-comp-r01-u26         | 240068-BTO      | 2024-01-26    | 10.10.23.20    | [☰](https://10.10.23.20) | 7c:c2:55:81:8c:0b | up to mac "7c:c2:55:81:8c:0d"    |

