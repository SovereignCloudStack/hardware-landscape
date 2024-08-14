# Netbox configuration templates

Configuration templates can be used to render device configurations from state defined in netbox, see [docs](https://netboxlabs.com/docs/netbox/en/stable/models/extras/configtemplate/).
Templates are written in the Jinja2 language and can be associated with devices roles, platforms, and/or individual devices.

This directory contains configuration templates for SCS hardware landscape network devices (SONiC switches).
These templates could be then imported to the netbox instance from git data source e.g. as [a data file objects](https://netboxlabs.com/docs/netbox/en/stable/models/core/datafile/).

For deeper understanding of how configuration rendering works in Netbox refer to the [docs](https://netboxlabs.com/docs/netbox/en/stable/features/configuration-rendering/).
Configuration templates use Netbox state of the resources (e.g. devices) and defined [context-data](https://netboxlabs.com/docs/netbox/en/stable/features/context-data/)
to render complete configuration files for each device on network.
Explore `*.j2` configuration templates in this directory and devices `local_context_data` definitions in 
`bootstrap/landscape` directory.
