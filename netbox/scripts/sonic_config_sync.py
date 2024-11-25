import tempfile
import datetime

from netmiko import ConnectHandler, file_transfer
from jinja2.exceptions import TemplateError

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


class SonicConfigSync(Script):
    class Meta:
        name = "Load NetBox Configuration onto SONiC Device"
        description = """Transfers NetBox configuration to SONiC device and loads it.
        
        **This script is not intended for production use!**
         
        It is a naive implementation of configuration synchronization that currently works only one-way,
        meaning it can only **add** missing parts to the SONiC device but cannot remove them. This will be improved.
        """

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
    def save_netbox_config_to_device(connection, netbox_config):
        """Save netbox config to the SONiC device and load it and save it."""
        # Generate the destination file name with the current date and time
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        dest_file = f"config_db_netbox_{timestamp}.json"

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
            # Load Netbox config to the runtime SONiC configuration
            connection.send_command(f"sudo config load /tmp/{dest_file} -y")
            # Save it
            connection.send_command(f"sudo config save -y")
        except Exception as err:
            raise ConnectionError(f"Sync of Netbox config failed: {err}")

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
            try:
                netbox_config = self.get_netbox_config(device)

                with self.get_device_connection(device) as connection:
                    self.save_netbox_config_to_device(connection, netbox_config)
                    self.log_success("NetBox configuration synced.", device)

            except ConnectionError as err:
                self.log_failure(f"Failed to sync NetBox configuration {err}.", device)
            except Exception as err:
                self.log_failure(f"Unexpected error on {device.name}: {err}", device)
