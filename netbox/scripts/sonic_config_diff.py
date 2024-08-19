import json
import difflib
import yaml
import re

from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoBaseException
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
from extras.scripts import Script, ObjectVar, AbortScript, MultiObjectVar

# Custom dumper to handle multiline strings
def str_presenter(dumper, data):
    if '\n' in data:  # Check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

# Add the custom string presenter
yaml.add_representer(str, str_presenter)


class ConnError(Exception):
    """"""

class CustomChoiceVar(ScriptVariable):
    form_field = ChoiceField

    def __init__(self, choices, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_attrs["choices"] = choices


def parse_current_configuration(frr_config):
    # Regular expression to match the "Current configuration:" and everything that follows
    match = re.search(r"Current configuration:\n(.+)", frr_config, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

class SonicConfigDiff(Script):
    class Meta:
        name = "Compare SONiC Configuration with NetBox Stored Configuration"
        description = "Fetches the current configuration from a SONiC device(s) via SSH and compares it with the configuration stored in NetBox."

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
            "username": "admin",  # FIXME: Use Netbox secret
            "password": "YourPaSsWoRd",  # FIXME: Use Netbox secret
            "port": 22,
        }
        try:
            return ConnectHandler(**sonic_device)
        except Exception as err:
            raise ConnError(f"Connection to SONiC device failed: {err}")

    @staticmethod
    def get_sonic_config_db(connection):
        try:
            return connection.send_command("sudo show runningconfiguration all")
        except Exception as err:
            raise ConnError(f"Retrieve SONiC config failed: {err}")

    @staticmethod
    def get_sonic_frr_conf(connection):
        try:
            frr_config = connection.send_command("sudo show runningconfiguration bgp")
        except Exception as err:
            raise ConnError(f"Retrieve SONiC config failed: {err}")

        return parse_current_configuration(frr_config)

    @staticmethod
    def get_netbox_config(device):
        context_data = device.get_config_context()
        context_data.update({"device": device})
        if config_template := device.get_config_template():
            try:
                return config_template.render(context=context_data)
            except TemplateError as err:
                raise ConnError(err)
        else:
            raise ConnError("Missing config template for device")


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
            netbox_config = None
            device_config = None
            try:
                with self.get_device_connection(device) as connection:
                    config_db_json = self.get_sonic_config_db(connection)
                    frr_conf = self.get_sonic_frr_conf(connection)
            except ConnError as err:
                device_err = err

            # FIXME: We have to join config_db.json and frr config into one yaml as follows:
            # ```yaml
            # config_db.json: |
            #   {
            #     ...
            #   }
            # frr.conf: |
            #   !
            #   frr version 8.1
            #   ...
            # ```
            # The reason is that current SCS Landscape SONiC switches do not utilize
            # frr-mgmt-framework yet
            # IMO is it a good idea to use that frr framework and simplify all the management
            # around with one and only one SONiC config file.

            # Nore: We have to use 2 spaces for indentation as the device config_db.json stored in Netbox
            # and in backups contains 2 spaces. SONiC's command `show runningconfig all` applies
            # 4 spaces. We have to adjust indentation to have a nice diff.
            if not device_err:
                config_db = json.dumps(json.loads(config_db_json), indent=2)
                device_config = yaml.dump({
                    "config_db.json": config_db,
                    "frr.conf": frr_conf
                }, default_flow_style=False)

                netbox_config = self.get_netbox_config(device)

                diff = difflib.unified_diff(
                    netbox_config.splitlines(),
                    device_config.splitlines(),
                    fromfile='NetBox config_db.json configuration',
                    tofile='SONiC running configuration',
                    lineterm='',
                )
                diff_out = "\n".join(diff).strip()

            compliance_device = ConplianceDeviceDataClass(
                pk=device.pk,
                name=device.name,
                mgmt_ip=str(device.primary_ip.address.ip),
                rendered_config=netbox_config,
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
            compliance_device.actual_config = device_config
            compliance_device.rendered_config = netbox_config
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
