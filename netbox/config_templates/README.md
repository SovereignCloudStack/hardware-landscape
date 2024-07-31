# Netbox configuration templates

Configuration templates can be used to render device configurations from state defined in netbox, see [docs](https://netboxlabs.com/docs/netbox/en/stable/models/extras/configtemplate/).
Templates are written in the Jinja2 language and can be associated with devices roles, platforms, and/or individual devices.

This directory contains configuration templates for SCS hardware landscape network devices (SONiC switches).
These templates could be then imported to the netbox instance from git data source e.g. as [a data file objects](https://netboxlabs.com/docs/netbox/en/stable/models/core/datafile/).

* DEVICE_METADATA
  * hostname: "st01-sw1g-r01-u47"
  * mac: "d2:77:ce:2b:44:c4"
  * type: "LeafRouter"
* MGMT_INTERFACE
  * mgmt_interface: "eth0"
  * mgmt_ip: "10.10.22.102"
  * mgmt_subnet: "24"
  * mgmt_gwaddr: "10.10.22.1"
* MGMT_PORT
  * mgmt_interface: "eth0"
* NTP_SERVER
  * ntp_servers: ["192.53.103.103", "192.53.103.104", "192.53.103.108"]
* PORT
  ```
  ports = {
    "Ethernet0": {
        "admin_status": "up",
        "alias": "Eth1(Port1)",
        "autoneg": "on",
        "description": "Uplink",
        "index": "1",
        "lanes": "26",
        "mtu": "9100",
        "parent_port": "Ethernet0",
        "speed": "1000"
    },
    ...
  }
  ```
* SNMP_COMMUNITY
  ```
  "snmp_communities": {
    "Eevaid7xoh4m": {"type": "RO"},
    "lohz3kaG5ted": {"type": "RW"},
    "public": {"type": "RO"}
  }
  ```
* STATIC_ROUTE
  ```
  static_routes = {
    "0.0.0.0/0": {
        "blackhole": "false,false,false",
        "distance": "0,0,0",
        "ifname": ",,",
        "nexthop": "10.10.23.1",
        "nexthop_vrf": ",,"
    }
    ...
  }
  ```
* SYSLOG_SERVER
  * syslog_servers: ["10.10.23.1"]
* VLAN
  ```
  vlans = {
      "Vlan23": {"vlanid": "23"},
      "Vlan24": {"vlanid": "24"},
      "Vlan25": {"vlanid": "25"},
      "Vlan26": {"vlanid": "26"}
  }
  ```
* VLAN_INTERFACE
  ```
  vlan_interfaces = {
      "Vlan23": None,
      "Vlan23|10.10.23.102/24": "10.10.23.102/24",
      "Vlan44": None,
      "Vlan44|10.20.30.40/24": "10.20.30.40/24",
      "Vlan45": None,
      "Vlan45|10.20.31.41/24": "10.20.31.41/24"
  }
  ```
* VLAN_MEMBER
  ```
  vlan_members = {
    "Vlan23|Ethernet0": {"tagging_mode": "tagged"},
    "Vlan23|Ethernet1": {"tagging_mode": "untagged"},
    "Vlan23|Ethernet10": {"tagging_mode": "untagged"},
    ...
  }
  ```

```json
{
   "hostname":"st01-sw1g-r01-u47",
   "mac":"d2:77:ce:2b:44:c4",
   "type":"LeafRouter",
   "mgmt_interface":"eth0",
   "mgmt_ip":"10.10.22.102",
   "mgmt_subnet":"24",
   "mgmt_gwaddr":"10.10.22.1",
   "ntp_servers":[
      "192.53.103.103",
      "192.53.103.104",
      "192.53.103.108"
   ],
   "ports":{
      "Ethernet0":{
         "admin_status":"up",
         "alias":"Eth1(Port1)",
         "autoneg":"on",
         "description":"Uplink",
         "index":"1",
         "lanes":"26",
         "mtu":"9100",
         "parent_port":"Ethernet0",
         "speed":"1000"
      }
   },
   "snmp_communities":{
      "Eevaid7xoh4m":{
         "type":"RO"
      },
      "lohz3kaG5ted":{
         "type":"RW"
      },
      "public":{
         "type":"RO"
      }
   },
   "static_routes":{
      "0.0.0.0/0":{
         "blackhole":"false,false,false",
         "distance":"0,0,0",
         "ifname":",,",
         "nexthop":"10.10.23.1",
         "nexthop_vrf":",,"
      }
   },
   "syslog_servers":[
      "10.10.23.1"
   ],
   "vlans":{
      "Vlan23":{
         "vlanid":"23"
      },
      "Vlan24":{
         "vlanid":"24"
      },
      "Vlan25":{
         "vlanid":"25"
      },
      "Vlan26":{
         "vlanid":"26"
      }
   },
   "vlan_interfaces":{
      "Vlan23":null,
      "Vlan23|10.10.23.102/24":"10.10.23.102/24",
      "Vlan44":null,
      "Vlan44|10.20.30.40/24":"10.20.30.40/24",
      "Vlan45":null,
      "Vlan45|10.20.31.41/24":"10.20.31.41/24"
   },
   "vlan_members":{
      "Vlan23|Ethernet0":{
         "tagging_mode":"tagged"
      },
      "Vlan23|Ethernet1":{
         "tagging_mode":"untagged"
      },
      "Vlan23|Ethernet10":{
         "tagging_mode":"untagged"
      }
   }
}
```

```json
{
  "mac_addr": "d2:77:ce:2b:44:c4",
  "mgmt_interface":"eth0",
  "mgmt_ip":"10.10.22.102",
  "mgmt_subnet":"24",
  "mgmt_gwaddr":"10.10.22.1",
}

```
https://github.com/netbox-community/netbox/issues/14277
https://github.com/wrouesnel/docker.netbox/blob/master/netbox/src/netbox/docs/administration/netbox-shell.md
