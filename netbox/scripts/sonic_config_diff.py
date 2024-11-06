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
from extras.scripts import Script, ObjectVar, AbortScript, MultiObjectVar


class ConnError(Exception):
    pass

class CustomChoiceVar(ScriptVariable):
    form_field = ChoiceField

    def __init__(self, choices, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_attrs["choices"] = choices


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
            "username": "admin",  # FIXME: Use Netbox secret to store the username
            "password": "YourPaSsWoRd",  # FIXME: Use Netbox secret to store the password
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
            except ConnError as err:
                device_err = err

            # Note: We have to use 2 spaces for indentation as the device config_db.json stored in Netbox
            # and in backups contains 2 spaces. SONiC's command `show runningconfig all` applies
            # 4 spaces. We have to adjust indentation to have a nice diff.
            if not device_err:
                device_config = json.dumps(json.loads(config_db_json), indent=2)
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
