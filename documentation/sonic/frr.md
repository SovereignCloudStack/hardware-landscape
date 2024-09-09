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
