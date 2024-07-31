import requests

from extras.scripts import Script, StringVar, ObjectVar, AbortScript
from dcim.models import Device, Interface


class UpdateSonicInterfacesFromINI(Script):
    class Meta:
        name = "Update SONiC Interfaces base on config_port.ini"
        # FIXME: commit_default does not work!
        # https://github.com/netbox-community/netbox/blob/develop/docs/customization/custom-scripts.md#commit_default
        commit_default = True
        description = """Fetch and update interface configurations based on the SONiC config_port.ini file available
        at SONiC Build Image Repository, https://github.com/sonic-net/sonic-buildimage. This ensures that SONiC-specific
        interface attributes like lanes, alias, index, and autoneg are populated.
        
        Example port_config.ini URL:
        https://raw.githubusercontent.com/sonic-net/sonic-buildimage/master/device/accton/x86_64-accton_as4630_54te-r0/Accton-AS4630-54TE/port_config.ini 
        
        Warning:
        The following custom fields must be available on the interface object in NetBox:
          - name: "lanes"
            type: "text"
            object_types: ["dcim.interface"]
          - name: "alias"
            type: "text"
            object_types: ["dcim.interface"]
          - name: "autoneg"
            type: "text"
            object_types: ["dcim.interface"]
          - name: "index"
            type: "text"
            object_types: ["dcim.interface"]
        """

    port_config_ini_url = StringVar(
        description="URL to fetch the SONiC port config file"
    )

    device = ObjectVar(
        description="Device to update interfaces for",
        model=Device
    )

    def get_sonic_port_config(self, url: str) -> dict:
        try:
            response = requests.get(url)
            response.raise_for_status()
            port_config_ini = response.text
        except requests.RequestException as e:
            raise AbortScript(f"Fetch SONiC port config request failed: {e}")

        sonic_port_config = {}

        lines = port_config_ini.strip().split("\n")
        for line in lines:
            # Skip comment or empty lines
            if line.startswith("#") or not line.strip():
                continue

            # Split the line into components and skip lines that don't have enough parts
            parts = line.split()
            if len(parts) < 6:
                continue

            # Extract port details
            name, lanes, alias, index, speed, autoneg = parts[:6]

            sonic_port_config[name] = {
                "lanes": lanes,
                "alias": alias,
                "index": index,
                "autoneg": autoneg,
            }
        self.log_info(f"SONiC port configuration fetched successfully")
        return sonic_port_config

    def update_interfaces(self, device, interfaces_config: dict):
        interfaces = Interface.objects.filter(device=device)
        for interface in interfaces:
            port_config = interfaces_config.get(interface.name)
            if port_config:
                try:
                    interface.custom_field_data = port_config

                    interface.full_clean()
                    interface.save()
                    self.log_success(f"{interface.name} updated successfully")
                except Exception as e:
                    self.log_failure(f"{interface.name} update failed: {e}")

                continue

            self.log_info(f"{interface.name} does not have a SONiC port configuration")

    def run(self, data, commit):
        port_config_url = data['port_config_ini_url']
        port_config = self.get_sonic_port_config(port_config_url)

        device = data['device']
        self.update_interfaces(device, port_config)

        self.log_success("All interfaces updated successfully.")
