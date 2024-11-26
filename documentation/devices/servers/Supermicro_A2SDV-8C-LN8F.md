
# Overview

* Model: Supermicro A2SDV-8C-LN8F
* Feature overview:
  * Intel
  * Single-CPU 8-Core Server:
    * [Intel(R) Atom(TM) CPU C3758 @ 2.20GHz](https://ark.intel.com/content/www/de/de/ark/products/97926/intel-atom-processor-c3758-16m-cache-up-to-2-20-ghz.html)
    * Low budget CPU, missing support for avx cpu instructions
      (no chance to run ovs/ovn instrastructure)
  * two 1+ Gbps
  * two 25 Gbps SFP+
    * NIC: enp2s0f0np0 / ASN: 65405
    * NIC: enp2s0f1np1 / ASN: 65404
  * 128 GB ECC RAM
  * two 480 GB SSD/NVMe
  * 1 HE
* Versions
  * Firmware Revision: 04.0
  * BIOS Version: 1.8	System
  * Redfish Version: 1.0.1
  * CPLD Version: 04.21.1
* References
  * [Vendor Information](https://www.supermicro.com/de/products/motherboard/a2sdv-8c-ln8f)
  * Specification: [A2SDV-8C-LN8F Motherboards Products Supermicro.pdf](https://github.com/SCS-Private/orga-infra/blob/main/scs-system-landscape/spec_sheets/servers//A2SDV-8C-LN8F_Motherboards_Products_Supermicro.pdf)
  * Licence Data: [orga-infra/ .. /supermicro-bmc-licences/<mac-adress>.txt](https://github.com/SCS-Private/orga-infra/tree/main/scs-system-landscape/supermicro-bmc-licences/)
* Application purpose / description:
  * Openstack Control
  * Ceph Mons
  * Ceph Object Gateways

# Hardware Overview


| Name             | Serial Number | Delivery date | Management IP  | ☰                        | MGMT MAC          | ASN        | Node IPv4   | Node IPv6                    | Comments                        |
|------------------|---------------|---------------|----------------|--------------------------|-------------------|------------|-------------|------------------------------|---------------------------------|
| st01-ctl-r01-u27 | 231206-BTO    | 2023-11-29    | 10.10.23.12    | [☰](https://10.10.23.12) | 3c:ec:ef:5b:b5:b9 | 4210021012 | 10.10.21.12 | fd0c:cc24:75a0:1:10:10:21:12 |                                 |
| st01-ctl-r01-u28 | 231207-BTO    | 2023-11-29    | 10.10.23.13    | [☰](https://10.10.23.13) | 3c:ec:ef:5b:b5:bf | 4210021013 | 10.10.21.13 | fd0c:cc24:75a0:1:10:10:21:13 |                                 |
| st01-ctl-r01-u29 | 231208-BTO    | 2023-11-29    | 10.10.23.14    | [☰](https://10.10.23.14) | 3c:ec:ef:5b:b5:bb | 4210021014 | 10.10.21.14 | fd0c:cc24:75a0:1:10:10:21:14 |                                 |
