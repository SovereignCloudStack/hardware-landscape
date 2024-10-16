# SONiC Zero Touch Provisioning

## ONIE

ONIE offers various methods for locating a Network Operating System (NOS) like the SONiC installer image.
For a comprehensive list of supported methods, refer to the [onie user-guide](https://opencomputeproject.github.io/onie/user-guide/index.html).

One such supported method is DHCP. A DHCP server can provide specific details about the location of the installer image
for ONIE. Basic DHCP scenarios and configuration examples can be found in [onie user-guide](https://opencomputeproject.github.io/onie/user-guide/index.html).

An advanced and more realistic scenario involving DHCP is Vendor Class Identifier matching.
When ONIE makes a DHCP request, it sets the DHCP vendor class (option 60) to a specific string.
Based on this, the DHCP server can select and return the appropriate installer image according to the machine type.

See an example for [ISC DHCP server](https://github.com/opencomputeproject/onie/blob/master/contrib/isc-dhcpd/dhcpd.conf)
where the Vendor Class Identifier is used to select installer image for accton_as7326_56x machine type.

```text
if option vendor-class-identifier = "onie_vendor:x86_64-accton_as7326_56x-r0" {
  option default-url "http://10.10.23.254:18080/Edgecore-SONiC_20240625_102433_ec202211_ecsonic_331.bin";
}
```

Alternatively, the administrator could define matching class as follows:

```text
class "onie-vendor-accton_as7326_56x-class" {
  match if substring(option vendor-class-identifier, 0, 27) = "onie_vendor:x86_64-accton_as7326_56x-r0";
  option default-url "http://10.10.23.254:18080/Edgecore-SONiC_20240625_102433_ec202211_ecsonic_331.bin";
}
```

## Zero Touch Provisioning (ZTP)

Zero Touch Provisioning (ZTP) in SONiC automates the initial setup of network devices without any user intervention.
When a SONiC device boots up for the first time, the ZTP service sends a DHCP request to obtain a location of the ZTP boot file.
The DHCP server provides the location of a boot file (utilizing DHCP option 67). This file is retrieved by the ZTP via TFTP,
HTTP, or another protocol.

The boot file contains information for ZTP to kick-start configuration steps of the device. This process bring the device
into operational state automatically.
ZTP service can be used by users to configure a fleet of switches using common configuration templates.

[ISC DHCP server](https://github.com/opencomputeproject/onie/blob/master/contrib/isc-dhcpd/dhcpd.conf) could be configured
to provide boot file location, e.g. as follows:

```text
option bootfile-name "http://10.10.23.254:18080/provision.json";
```

Refer to the [docs](https://github.com/sonic-net/SONiC/blob/master/doc/ztp/ztp.md) for detailed information on how to
create ZTP boot file.
