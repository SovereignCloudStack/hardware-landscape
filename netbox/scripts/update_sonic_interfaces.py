import requests

from extras.scripts import Script, StringVar, ObjectVar, AbortScript, BooleanVar
from dcim.models import Device, Interface


BREAKOUT_MODE_MAP = {"1000": "1x1G", "25000": "1x25G[10G,1G]", "100000": "1x100G[40G]"}


class UpdateSonicInterfacesFromINI(Script):
    class Meta:
        name = "Update SONiC Interfaces base on config_port.ini"
        # FIXME: commit_default does not work!
        # https://github.com/netbox-community/netbox/blob/develop/docs/customization/custom-scripts.md#commit_default
        commit_default = True
        description = """Fetch and update interface configurations based on the SONiC config_port.ini file available
        at SONiC Build Image Repository, https://github.com/sonic-net/sonic-buildimage. This ensures that SONiC-specific
        interface attributes like lanes, alias, index, brkout_mode, and autoneg are populated.
        
        Optionally, you can disable all ports by using the Disable ports script option.
        
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
          - name: "brkout_mode"
            type: "text"
            object_types: [ "dcim.interface" ]
        """

    port_config_ini_url = StringVar(
        description="URL to fetch the SONiC port config file", label="Port config URL"
    )

    device = ObjectVar(
        description="Device to update interfaces for", label="Device", model=Device
    )

    disable_ports = BooleanVar(
        description="Disable every port listed in the port configuration file",
        label="Disable ports",
        default=False,
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
                "speed": speed,
                "brkout_mode": BREAKOUT_MODE_MAP[speed],
                "lanes": lanes,
                "alias": alias,
                "index": index,
                "autoneg": autoneg,
            }
        self.log_info(f"SONiC port configuration fetched successfully")
        return sonic_port_config

    def update_interfaces(
        self, device, interfaces_config: dict, disable_ports: bool = False
    ):
        interfaces = Interface.objects.filter(device=device)
        for interface in interfaces:
            port_config = interfaces_config.get(interface.name)
            if port_config:
                try:
                    if disable_ports:
                        interface.enabled = False

                    speed = port_config.pop(
                        "speed"
                    )  # speed is regular interface field, not a custom one
                    interface.speed = (
                        int(speed) * 1000
                    )  # port config contains speed in Mbps, netbox expects bps

                    interface.custom_field_data = port_config

                    interface.full_clean()
                    interface.save()
                    self.log_success(f"{interface.name} updated successfully")
                except Exception as e:
                    self.log_failure(f"{interface.name} update failed: {e}")

                continue

            self.log_info(f"{interface.name} does not have a SONiC port configuration")

    def run(self, data, commit):
        port_config = self.get_sonic_port_config(data["port_config_ini_url"])
        self.update_interfaces(data["device"], port_config, data["disable_ports"])

        self.log_success("All interfaces updated successfully.")
