# Initialize Netbox

NetBox starts with no data following its initial deployment.
To effectively add and configure network devices, some basic
setup is necessary.

This tutorial provides scripts and instructions to bootstrap NetBox with minimal
prerequisites, enabling you to add network devices and manage their configurations.

## Prerequisites 

* Create virtual environment and install python dependencies (recommended)
  ```bash
  python3 -m venv .venv --prompt bootstrap
  source .venv/bin/activate
  # Install dependencies
  pip install -r requirements.txt
  ```

## Initialize bases

The script `netbox_base.py` is custom-designed and initializes the following:
* site (ST01)
* rack (Landscape) on site ST01
* device roles (ManagementRouter, SpineRouter, LeafRouter)
* platform (SONiC)
* manufacturer (Endgecore)
* interface custom fields (Lanes, Alias, Autoneg, Index)

```bash
./netbox_init.py --api-url <netbox-url> --api-token <netbox-token> --data-file base.yml
```

The upstream script https://github.com/netbox-community/Device-Type-Library-Import
facilitates importing of device types, available at https://github.com/netbox-community/devicetype-library.
The following imports all `edgecore` device types. Note that the SCS fork is used here, as the [#2276](https://github.com/netbox-community/devicetype-library/pull/2276)
is not merged yet.

Note that REPO_URL and  REPO_BRANCH override could be removed after [#2276](https://github.com/netbox-community/devicetype-library/pull/2276) is merged

```bash
docker run --rm --network host \
  -e REPO_URL=https://github.com/SovereignCloudStack/devicetype-library/ \
  -e REPO_BRANCH=edgecore \
  -e VENDORS=edgecore \
  -e NETBOX_URL=<netbox-url> \
  -e NETBOX_TOKEN=<netbox-token> \
  ghcr.io/minitriga/netbox-device-type-library-import
```

## Initialize devices