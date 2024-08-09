# Initialize SCS Landscape in Netbox

NetBox starts with no data following its initial deployment.
To effectively add and configure network devices, some setup is necessary.

This tutorial provides scripts and instructions to bootstrap NetBox with
prerequisites, enabling you to add SCS Landscape network devices and manage their configurations.

Note that the tutorial is not limited to SCS Landscape. The reader could create own YAML definitions
of required initialization in Netbox.

## Prerequisites 

* Create virtual environment (recommended) and install python dependencies
  ```bash
  # Create virtual environment (recommended)
  python3 -m venv .venv --prompt bootstrap
  source .venv/bin/activate
  # Install dependencies
  pip install -r requirements.txt
  ```

## Initialize device types

The upstream script https://github.com/netbox-community/Device-Type-Library-Import
facilitates importing of device types, available at https://github.com/netbox-community/devicetype-library.
The following command imports all `edgecore` device types.

Note that the SCS fork is used here, as the [#2276](https://github.com/netbox-community/devicetype-library/pull/2276) is not merged yet, therefore the REPO_URL and REPO_BRANCH
overrides could be removed after #2276.

```bash
docker run --rm --network host \
  -e REPO_URL=https://github.com/SovereignCloudStack/devicetype-library/ \
  -e REPO_BRANCH=edgecore \
  -e VENDORS=edgecore \
  -e NETBOX_URL=<netbox-url> \
  -e NETBOX_TOKEN=<netbox-token> \
  ghcr.io/minitriga/netbox-device-type-library-import
```

## Import Netbox custom scripts
TODO

## Import SCS Landscape

The script `netbox_init.py` is custom-designed and initializes the Landscape DCIM/IPAM 
infrastructure as is defined in the `landscape` directory. Explore the human readable `yaml`
definitions of the current Landscape state.
The script facilitates the initial bootstrapping of fresh Netbox instance, further testing and
development of SCS Landscape.

Note that the script is not limited to SCS Landscape. The reader could create own YAML definitions
of required initialization in Netbox.

```bash
./netbox_init.py --api-url <netbox-url> --api-token <netbox-token> --sync-datasources --execute-scripts --data-dir landscape
```
