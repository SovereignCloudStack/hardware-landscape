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

Custom scripting provides a way for users to execute custom logic from within the NetBox, see [docs](https://netbox.uemasul.edu.br/static/docs/customization/custom-scripts/).

To add custom scripts to your NetBox installation, scripts should be saved to `/opt/netbox/netbox/scripts`.
If you are running netbox-docker then mount scripts defined in this repository on path 
`/hardware-landscape/netbox/scripts` into the desired netbox directory e.g. as follows:
```yaml
  netbox:
    volumes:
    - ./hardware-landscape/netbox/scripts:/etc/netbox/scripts:z,ro
 ```
Adjust accordingly, based on your directory structure and location of the Netbox docker-compose.yml file.

Alternatively, custom scripts could be uploaded to NetBox from a remote data source like a Git repo or S3 bucket. 
To add `SovereignCloudStack/hardware-landscape` Git data source, use the `netbox_init.py` script as follows:

```bash
./netbox_init.py --api-url <netbox-url> --api-token <netbox-token> --sync-datasources --data-file landscape/03_data_sources.yml
```

Navigate to `Customization/Scripts` and from here you can click the link to add `update_sonic_interfaces.py` script from
remote data source `scs-hardware-landscape`.
Refer to [this blog post](https://netboxlabs.com/blog/getting-started-with-netbox-custom-scripts/) for further details. 

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
