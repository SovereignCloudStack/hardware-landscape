# FRR

[FRRouting](https://frrouting.org/) (Free Range Routing, FRR) is a free and open-source internet routing protocol suite
designed for Linux and Unix platforms. It provides comprehensive support for key routing protocols including BGP, OSPF,
RIP, IS-IS, PIM, LDP, BFD, Babel, PBR, OpenFabric, and VRRP. Additionally, it offers alpha-level support for EIGRP and NHRP,
making it highly versatile for a wide range of networking environments. 

FRR is widely used for both enterprise and service provider networks due to its flexibility, scalability, and adherence
to open standards. Refer to [docs](https://github.com/sonic-net/sonic-frr/blob/master/doc/user/overview.rst) for more details.

## FRR in SONiC

While FRR offers extensive protocol support, SONiC does not fully implement all of its capabilities. SONiC provides 
**three** different configuration modes, each governing how the FRR configuration is created and managed.

Two of these modes are **integrated**, where the FRR configuration is automatically generated from the SONiC configuration (config_db.json).
The third mode involves a **split** configuration approach, where both the SONiC configuration model and the FRR configuration
model are used in tandem.

### Integrated FRR configuration

When the BGP container in SONiC starts, it generates the FRR configuration based on data stored in the REDIS database,
which comes from the `/etc/sonic/config_db.json` file. The configuration is first validated using YANG models and then
loaded into REDIS. Services in the system use REDIS to get this configuration.

Integrated FRR configuration is enabled by the `docker_routing_config_mode` option under DEVICE_METADATA table.
Two from four options of `docker_routing_config_mode` enable integrated FRR configuration:
- `separated`: FRR config generated from ConfigDB, each FRR daemon has its own config file
- `unified`: FRR config generated from ConfigDB, single FRR config file

Inside the BGP container, Jinja templates are used to convert the REDIS data into FRR configuration syntax.
SONiC has two ways to manage FRR configuration, both handled by daemons in the BGP container:
- **sonic-bgpcfgd**
  This is the default (template based) legacy `bgpcfgd` daemon. It supports BGP, static routes, BFD, and BGPmon. Some settings can be updated 
  without restarting the bgp container, but others require a restart. The Jinja templates show which settings are dynamic.

- **sonic-frr-mgmt-framework**
  This new FRR config is fully based on config-DB events, and it is implemented within `frrcfgd` daemon. It supports more protocols, including OSPF, VRFs, L2 EVPN, IGMP, and PIM. It automatically updates
  the FRR configuration when changes are made to REDIS, but it's less [documented](https://github.com/sonic-net/SONiC/blob/master/doc/mgmt/SONiC_Design_Doc_Unified_FRR_Mgmt_Interface.md)
  and may require looking at the underlying [frrcfgd code](https://github.com/sonic-net/sonic-buildimage/blob/master/src/sonic-frr-mgmt-framework/frrcfgd/frrcfgd.py).

To enable the newer sonic-frr-mgmt-framework daemon, the `frr_mgmt_framework_config` field must be set to "true" in the DEVICE_METADATA table.

Any manual changes made with VTYSH or other FRR tools are not saved after a restart. On restart, the configuration is regenerated from the SONiC configuration.

Here's an example configuration in DEVICE_METADATA:
```json
"DEVICE_METADATA": {
    "localhost": {
        ...
        "hostname": "sonic",
        "docker_router_config_mode": "unified",
        "frr_mgmt_framework_config": "true"  # for bgpcfgd set "false" 
        ...
    }
}
```

### Split FRR configuration

Split configuration was introduced upstream in May 2023 and is widely used in enterprise versions of SONiC. This mode 
allows changes made through FRR’s native tools, like VTYSH, to be saved and persist across reboots. However, this comes
at the cost of no longer using SONiC’s configuration database to manage the FRR configuration.

Key points about split configuration:
- At startup, if only a SONiC configuration exists and no FRR configuration is present, an FRR configuration will be generated from the SONiC configuration.
- If an FRR configuration already exists, it will be used instead of generating a new one from the SONiC configuration.
- Any changes made using FRR tools (like VTYSH) will persist through reboots when saved.

Split mode is enabled in the DEVICE_METADATA table by setting the docker_router_config_mode field.
Two from four options of `docker_routing_config_mode` enable split FRR configuration:
- `split`: FRR config is not generated from ConfigDB, and each FRR daemon has its own config file
- `split-unified`: FRR config is not generated from ConfigDB, and a single FRR config file is used

Once split mode is enabled, SONiC will no longer update the FRR configuration from its own configuration database.
All future configuration changes must be made using FRR tools, such as VTYSH.

Here's an example configuration in DEVICE_METADATA:
```json
"DEVICE_METADATA": {
    "localhost": {
        ...
        "hostname": "sonic",
        "docker_router_config_mode": "split-unified",
        ...
    }
}
```


## Which FRR configuration model should I use in SONiC?

When choosing a configuration model in SONiC, it’s important to match your needs with the available protocol and parameter support:

- Split mode
  - Allows configurations made through FRR tools like VTYSH to persist across reboots
  - However, it requires maintaining **two** separate configuration systems: SONiC’s ConfigDB and FRR’s native configuration files
  - Some voices (e.g. read [this](https://medium.com/sonic-nos/sonic-dont-use-split-mode-use-frr-mgmt-framework-a67ad76ec1a6)) do not recommend it for production due to the increased complexity in managing and automating configurations
  - All configurations must be managed through FRR tools, as SONiC will no longer control the FRR settings.

- Integrated mode - sonic-bgpcfgd (default model)
  - Best for simple setups
  - Supports BGP, static routes, BFD, and BGPmon
  - Based on YANG models, making it easier to configure without inspecting the source code
  - Recommended if it covers the protocols you need

 - Integrated mode - sonic-frr-mgmt-framework (frrcfgd)
   - Suitable for more advanced configurations
   - Supports additional protocols like OSPF, VRFs, L2 EVPN, PIM, and IGMP
   - Less documentation is available, so reviewing the source code (particularly frrcfgd.py) may be required

## Which FRR configuration options are not supported in the integrated mode with sonic-frr-mgmt-framework (frrcfgd)?

Before opting for the integrated mode with the SONiC-FRR management framework (frrcfgd), be aware that not all FRR
configuration options are supported.
As previously mentioned, the documentation for the sonic-frr-mgmt-framework is incomplete, and reviewing the frrcfgd.py
code is necessary to determine which FRR options are supported and which are not.

For example, the FRR route map option [set src ADDRESS](https://docs.frrouting.org/en/stable-7.1/zebra.html#clicmd-setsrcADDRESS)
can be configured using FRR's vtysh but appears to be missing in the unified FRR management interface.
See the related documentation [here](https://github.com/sonic-net/SONiC/blob/master/doc/mgmt/SONiC_Design_Doc_Unified_FRR_Mgmt_Interface.md#321101-route_map).
To verify further, review the corresponding section in the frrcfgd.py file [here](https://github.com/sonic-net/sonic-buildimage/blob/master/src/sonic-frr-mgmt-framework/frrcfgd/frrcfgd.py#L1862).


## What about enterprise Edge-core SONiC?

Edgecore officially provides builds of enterprise Edge-core SONiC images for the following branches:
- SONiC.202211
- SONiC.202111
- SONiC.202012
- SONiC.202006
- SONiC.201911

TL;DR: Avoid using the integrated mode with the SONiC-FRR management framework (frrcfgd) on these versions!

These builds do not include a [bug fix](https://github.com/edge-core/sonic-buildimage/commit/fabb30f2e98db967064daed757aeb221bee0c323)
for frrcfgd, which is required for the unified FRR configuration to function properly.
This fix is only available in the following Edgecore SONiC branches: 202305, 202311, 202311.0, 202311.X, master, and pre_202305.

Without this fix, the FRR management framework does not behave as expected. Specifically, frrcfgd fails to interpret the
Config DB BGP entries correctly, leading to errors such as:

```text
Sep 11 09:53:08.188862 st01-sw1g-r01-u42 INFO bgp#frrcfgd: value for table BGP_PEER_GROUP prefix default key LEAF changed to {'admin_status': (true, ADD), 'asn': (65501, ADD), 'peer_type': (external, ADD)}
Sep 11 09:53:08.190100 st01-sw1g-r01-u42 DEBUG bgp#frrcfgd: execute command vtysh -c 'configure terminal' -c 'router bgp 65000 vrf default' -c 'neighbor LEAF remote-as 65501' for table BGP_PEER_GROUP.
Sep 11 09:53:08.190100 st01-sw1g-r01-u42 DEBUG bgp#frrcfgd: VTYSH CMD: configure terminal daemons: ['bgpd']
Sep 11 09:53:08.190100 st01-sw1g-r01-u42 DEBUG bgp#frrcfgd: VTYSH CMD: router bgp 65000 vrf default daemons: ['bgpd']
Sep 11 09:53:08.190100 st01-sw1g-r01-u42 DEBUG bgp#frrcfgd: VTYSH CMD: neighbor LEAF remote-as 65501 daemons: ['bgpd']
Sep 11 09:53:08.190132 st01-sw1g-r01-u42 DEBUG bgp#frrcfgd: [bgpd] command return code: 13
Sep 11 09:53:08.190132 st01-sw1g-r01-u42 DEBUG bgp#frrcfgd: % Create the peer-group or interface first
Sep 11 09:53:08.190147 st01-sw1g-r01-u42 DEBUG bgp#frrcfgd: VTYSH CMD: end daemons: ['bgpd']
Sep 11 09:53:08.190174 st01-sw1g-r01-u42 ERR bgp#frrcfgd: command execution failure. Command: "vtysh -c 'configure terminal' -c 'router bgp 65000 vrf default' -c 'neighbor LEAF remote-as 65501'"
Sep 11 09:53:08.190174 st01-sw1g-r01-u42 ERR bgp#frrcfgd: failed running FRR command: neighbor LEAF remote-as 65501
```
In this case, frrcfgd recognizes the BGP_PEER_GROUP, but it fails to translate it into proper FRR-BGP CLI commands.

After manually applying the fix to the SONiC.202211 build, the FRR management framework functioned as expected, enabling
the unified FRR configuration to work properly.
