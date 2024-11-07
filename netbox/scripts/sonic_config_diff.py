import json
import difflib

from netmiko import ConnectHandler
from jinja2.exceptions import TemplateError
from netutils.config.compliance import diff_network_config

from netbox_config_diff.models import ConplianceDeviceDataClass

from django.forms import ChoiceField
from extras.scripts import ScriptVariable
from dcim.choices import DeviceStatusChoices
from dcim.models import Device, DeviceRole, Site
from django.conf import settings
from django.db.models import Q
from dcim.models import Device
from utilities.exceptions import AbortScript
from extras.scripts import Script, ObjectVar, MultiObjectVar


class ConnectionError(Exception):
    pass


class ConfigError(Exception):
    pass


class CustomChoiceVar(ScriptVariable):
    form_field = ChoiceField

    def __init__(self, choices, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_attrs["choices"] = choices


def filter_dict(destination, source):
    """
    Filters a dictionary (destination) to only include keys found in another dictionary (source).
    Includes top-level keys from source if they are empty in source, while filtering nested keys based on source.

    Parameters:
    - destination (dict): The dictionary from which we want to extract keys.
    - source (dict): The dictionary specifying the keys (including nested) to keep in the destination.

    Returns:
    - dict: A filtered dictionary containing only keys from the source. Top-level keys are included if empty in source.

    Example:
    ```
    destination = {
        "a": {"b": 1, "c": {}},
        "d": {"e": None, "f": {"g": 2, "h": {}}},
        "i": {"j": {"k": 4}}
    }

    source = {
        "a": {"b": {}, "c": {}},
        "d": {"f": {"g": {}, "h": {}}},
        "i": {"j": {"k": {}}},
        "x": {}
    }

    result = filter_dict(destination, source)
    # Result will be:
    # {
    #     "a": {"b": 1, "c": {}},
    #     "d": {"f": {"g": 2, "h": {}}},
    #     "i": {"j": {"k": 4}},
    #     "x": {}
    # }
    ```
    """

    def recursive_filter(dest, src):
        filtered = {}

        for key, sub_key_dict in src.items():
            # Include top-level empty keys from source even if they don’t exist in destination
            if key in dest:
                if isinstance(sub_key_dict, dict) and isinstance(dest[key], dict):
                    # Keep nested structure according to source
                    filtered[key] = recursive_filter(dest[key], sub_key_dict)
                else:
                    # Add value from destination if it exists
                    filtered[key] = dest[key]
            elif isinstance(sub_key_dict, dict) and not sub_key_dict:
                # Add top-level empty structure if key is empty in source and not in destination
                filtered[key] = {}

        return filtered

    return recursive_filter(destination, source)


def sort_dict(item: dict):
    for k, v in sorted(item.items()):
        item[k] = sorted(v) if isinstance(v, list) else v

    return {k: sort_dict(v) if isinstance(v, dict) else v for k, v in sorted(item.items())}


class SonicConfigDiff(Script):
    class Meta:
        name = "Compare SONiC Configuration with NetBox Stored Configuration"
        description = "Fetches the current configuration from a SONiC device(s) via SSH and compares it with the configuration stored in NetBox. It compares only keys available in the NetBox configuration."

    site = ObjectVar(
        model=Site,
        required=False,
        description="Run compliance for devices (with primary IP, platform) in this site",
    )
    role = ObjectVar(
        model=DeviceRole,
        required=False,
        description="Run compliance for devices with this role",
    )
    devices = MultiObjectVar(
        model=Device,
        required=False,
        query_params={
            "has_primary_ip": True,
        },
        description="If you define devices in this field, Site, Role fields will be ignored",
    )
    status = CustomChoiceVar(
        choices=DeviceStatusChoices,
        default=DeviceStatusChoices.STATUS_ACTIVE,
    )

    @staticmethod
    def get_device_connection(device):
        sonic_device = {
            "device_type": "linux",
            "host": str(device.primary_ip.address.ip),
            "username": "admin",  # FIXME: Use Netbox secret to store the username
            "password": "YourPaSsWoRd",  # FIXME: Use Netbox secret to store the password
            "port": 22,
        }
        try:
            return ConnectHandler(**sonic_device)
        except Exception as err:
            raise ConnectionError(f"Connection to SONiC device failed: {err}")

    @staticmethod
    def get_sonic_config_db(connection):
        try:
            return connection.send_command("sudo show runningconfiguration all")
        except Exception as err:
            raise ConnectionError(f"Retrieve SONiC config failed: {err}")

    @staticmethod
    def get_netbox_config(device):
        context_data = device.get_config_context()
        context_data.update({"device": device})
        if config_template := device.get_config_template():
            try:
                return config_template.render(context=context_data)
            except TemplateError as err:
                raise ConnectionError(err)
        else:
            raise ConnectionError("Missing config template for device")

    def validate_data(self, data: dict):
        if not data["site"] and not data["role"] and not data["devices"]:
            raise AbortScript("Define site, role or devices")

        if data["devices"]:
            devices = (
                data["devices"]
                .filter(
                    status=data["status"],
                )
                .exclude(
                    Q(primary_ip4__isnull=True) & Q(primary_ip6__isnull=True),
                )
            )
        else:
            filters = {
                "status": data["status"],
            }
            if data["site"]:
                filters["site"] = data["site"]
            elif data["role"]:
                if settings.VERSION.split(".", 1)[1].startswith("5"):
                    filters["device_role"] = data["role"]
                else:
                    filters["role"] = data["role"]
            devices = Device.objects.filter(**filters).exclude(
                Q(primary_ip4__isnull=True) & Q(primary_ip6__isnull=True),
            )

        if not devices:
            self.log_warning(
                "No matching devices found, devices must have primary IP"
            )
        else:
            self.log_info(f"Working with device(s): {', '.join(d.name for d in devices)}")
        return devices

    def run(self, data, commit):
        devices = self.validate_data(data)
        for device in devices:

            device_err = None
            diff_out = None
            netbox_config_sorted = None
            device_config_sorted = None
            try:
                with self.get_device_connection(device) as connection:
                    config_db = self.get_sonic_config_db(connection)
            except ConnectionError as err:
                device_err = err

            if not device_err:
                netbox_config = json.loads(self.get_netbox_config(device))
                netbox_config_sorted = json.dumps(sort_dict(netbox_config), indent=2)

                # Note: We have to use 2 spaces for indentation as the device config_db.json stored in Netbox
                # and in backups contains 2 spaces. SONiC's command `show runningconfig all` applies
                # 4 spaces. We have to adjust indentation to have a nice diff.
                device_config_filtered = filter_dict(json.loads(config_db), netbox_config)
                device_config_sorted = json.dumps(sort_dict(device_config_filtered), indent=2)

                diff = difflib.unified_diff(
                    netbox_config_sorted.splitlines(),
                    device_config_sorted.splitlines(),
                    fromfile='NetBox config_db.json configuration',
                    tofile='SONiC running configuration',
                    lineterm='',
                )
                diff_out = "\n".join(diff).strip()

            compliance_device = ConplianceDeviceDataClass(
                pk=device.pk,
                name=device.name,
                mgmt_ip=str(device.primary_ip.address.ip),
                rendered_config=netbox_config_sorted,
                device=device,
                # Note: Below are just a placeholders, sonic platform is not supported yet,
                # and `ConplianceDeviceDataClass` is not used to retrieve config from device yet.
                platform="sonic",
                command="",
                username=None,
                password=None,
            )
            compliance_device.error = device_err
            compliance_device.diff = diff_out
            compliance_device.actual_config = device_config_sorted
            compliance_device.rendered_config = netbox_config_sorted
            if not device_err:
                # FIXME: SONiC is not supported in netutils, so we have to use "some" supported platform here
                compliance_device.missing = diff_network_config(
                    compliance_device.rendered_config, compliance_device.actual_config, "arista_eos"
                )
                compliance_device.extra = diff_network_config(
                    compliance_device.actual_config, compliance_device.rendered_config, "arista_eos"
                )
            compliance_device.send_to_db()

            if diff_out:
                self.log_warning("Differences found between NetBox and SONiC configuration.", device)
            elif device_err:
                self.log_failure("Failed to check differences", device)
            else:
                self.log_success("No differences found between NetBox and SONiC configuration.", device)
