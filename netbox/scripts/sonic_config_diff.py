import json
import difflib
import tempfile

from netmiko import ConnectHandler, file_transfer
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


# FIXME: Certain keys need to be excluded from the running SONiC configuration as well as from Netbox config
#  to produce a cleaner diff with the NetBox configuration merged with the initial SONiC config.
#  This is necessary because the NetBox config lacks some keys present in the running configuration.
#  This process could be improved by finding a better way to generate and merge the NetBox config with
#  the initial and any other relevant configurations, aiming to more closely match the running configuration.
CONFIG_DB_SKIP_KEYS = (
    "FEATURE",
    "FLEX_COUNTER_TABLE",
    "LOGGER",
    "PORT",
    "SNMP",
    "SNMP_COMMUNITY",
    "VERSIONS",
    "bgpraw"
)


class ConnectionError(Exception):
    pass


class ConfigError(Exception):
    pass


class CustomChoiceVar(ScriptVariable):
    form_field = ChoiceField

    def __init__(self, choices, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_attrs["choices"] = choices


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
    def get_sonic_merged_config(connection, netbox_config):
        """Save netbox config to the sonic device and merge it wit the init sonic config.

        This function ensures that the config stored in the Netbox is merged with the
        SONiC init configuration `init_cfg.json` utilizing the `sonic-cfggen` tool.
        Then we could compare the merged config (output of this function) with the
        SONiC running configuration and calculate diff between them.
        """
        dest_file = "netbox_config.json"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
            temp_file.write(netbox_config.encode("utf-8"))

            try:
                file_transfer(
                    connection,
                    source_file=temp_file.name,
                    dest_file=dest_file,
                    file_system="/tmp"
                )
            except Exception as err:
                raise ConnectionError(f"Transfer of Netbox config failed: {err}")

        try:
            result = connection.send_command(f"sudo sonic-cfggen -j /etc/sonic/init_cfg.json -j /tmp/{dest_file} --print-data")
            # Remove tmp file
            connection.send_command(f"sudo rm /tmp/{dest_file}")
        except Exception as err:
            raise ConnectionError(f"Retrieve SONiC config failed: {err}")

        return result

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

            netbox_config = self.get_netbox_config(device)
            try:
                with self.get_device_connection(device) as connection:
                    config_db = self.get_sonic_config_db(connection)
                    netbox_merged = self.get_sonic_merged_config(connection, netbox_config)

            except ConnectionError as err:
                device_err = err

            if not device_err:

                config_db_json = json.loads(config_db)
                netbox_merged_json = json.loads(netbox_merged)
                netbox_merged_filtered = {k: v for k, v in netbox_merged_json.items() if k not in CONFIG_DB_SKIP_KEYS and v}
                config_db_filtered = {k: v for k, v in config_db_json.items() if k not in CONFIG_DB_SKIP_KEYS and v}

                netbox_config_sorted = json.dumps(sort_dict(netbox_merged_filtered), indent=2)
                device_config_sorted = json.dumps(sort_dict(config_db_filtered), indent=2)

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
