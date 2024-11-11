# Open Network Install Environment (ONIE)

ONIE is an open-source Linux-based boot loader designed for bare-metal network switches. Created by Cumulus Networks
in 2012, ONIE enables switches to automatically find and install a network operating system (NOS) of the user’s choice,
offering flexibility across hardware.

Key features of ONIE:
- Vendor-Neutral: ONIE supports multiple NOS options, so users aren’t locked into a specific vendor’s software
- Linux-Based: ONIE includes basic tools from BusyBox and operates on a lightweight Linux environment
- Open Compute Project (OCP) Support: Since 2013, OCP has backed ONIE, leading to wider adoption across different
  hardware and software vendors

When a switch with ONIE is turned on, it boots in discovery mode, finds a suitable NOS, and installs it automatically,
simplifying network setups and supporting scalable network growth.

Together, ZTP and ONIE help create flexible, efficient, and scalable networks, particularly useful in cloud and data
center environments.

## Configuration

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
  option default-url "http://<http-server>/<installer-image>.bin";
}
```

Alternatively, the administrator could define matching class as follows:

```text
class "onie-vendor-accton_as7326_56x-class" {
  match if substring(option vendor-class-identifier, 0, 27) = "onie_vendor:x86_64-accton_as7326_56x-r0";
  option default-url "http://<http-server>/<installer-image>.bin";
}
```
