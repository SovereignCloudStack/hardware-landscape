# Zero Touch Provisioning (ZTP)

ZTP automates the setup of network devices like routers and switches without needing manual configuration.
When shipped directly to a site, a device can connect to the network, download its configuration files,
and start working automatically. This process helps reduce errors, saves time, and makes it easier to
scale networks quickly.

ZTP typically involves:
- Automatic Network Connection: The device connects to the network as soon as it’s powered on
- Configuration Download: It retrieves its configuration and, if needed, software updates from a server
- Custom Script Execution: Additional settings or actions can be applied through scripts, making ZTP flexible for different needs

ZTP is popular in large networks and data centers, where it speeds up deployments and reduces manual effort.

## Configuration

ZTP in SONiC automates the initial setup of network devices without any user intervention. When a SONiC device boots up
for the first time, the ZTP service sends a DHCP request to obtain a location of the ZTP boot file.
The DHCP server provides the location of a boot file (utilizing DHCP option 67). This file is retrieved by the ZTP via TFTP,
HTTP, or another protocol.

The boot file contains information for ZTP to kick-start configuration steps of the device. This process bring the device
into operational state automatically.

[ISC DHCP server](https://github.com/opencomputeproject/onie/blob/master/contrib/isc-dhcpd/dhcpd.conf) could be configured to provide boot file location, e.g. as follows:

```text
option bootfile-name "http://<http-server>/provision.json";
```

Refer to the [docs](https://github.com/sonic-net/SONiC/blob/master/doc/ztp/ztp.md) for detailed information on how to
create ZTP boot file.

See and example of `ztp.json` file (for full list of supported ZTP plugins like snmp, firmware, etc. and available
options refer to the [docs](https://github.com/sonic-net/SONiC/blob/master/doc/ztp/ztp.md)):

```json
{
  "ztp": {
    "01-configdb-json": {
      "dynamic-url": {
        "source": {
          "prefix": "http://<http-server>/",
          "identifier": "hostname",
          "suffix": "_config_db.json"
        }
      }
    },
    "02-provisioning-script": {
      "plugin": {
        "url":"http://<http-server>/post_install.sh"
      },
      "reboot-on-success": true
    },
    "03-connectivity-check": {
      "ping-hosts": [ "1.1.1.1" ]
    }
  }
}
```

## ZTP in SONiC community version

ZTP is not enabled by default in SONiC community images:
```bash
$ show ztp status
ZTP feature unavailable in this image version
```

To enable ZTP in SONiC community, you'll need to build your own image with the `ENABLE_ZTP = y` option, which adds ZTP
support, or enable it  once the NOS is booted via `sudo config ztp enable`.
Note that the SONiC Edge-core enterprise image comes with ZTP enabled by default.
