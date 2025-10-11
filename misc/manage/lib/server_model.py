import glob
import logging
import os
import re
import sys

from .global_helpers import get_basedir, decrypt_vault_yaml_file
from .helpers import get_unique

LOGGER = logging.getLogger()

CONFIG_FIELDS_SERVERS = ['name', 'serial', 'bmc_ip_v4', 'bmc_mac', 'node_ip_v4',
                         'node_ip_v6', 'bmc_password', 'bmc_username', 'interfaces']


def get_server_documentation_dir() -> str:
    return f"{get_basedir()}/documentation/devices/servers/"


def get_bmc_login_data(name: str) -> tuple[str,str]:
    # Moved that to 99_bmc_secret.yml.disabled to ignore that file by ansible
    # see https://github.com/osism/issues/issues/1167
    bmc_login_data_secret_file = f"{get_basedir()}/inventory/host_vars/{name}/99_bmc_secret.yml.disabled"

    if not os.path.isfile(bmc_login_data_secret_file):
        LOGGER.error(f"Unable to open the bmc server secrets file {bmc_login_data_secret_file}")
        sys.exit(1)

    data = decrypt_vault_yaml_file(bmc_login_data_secret_file)
    bmc_user=data["bmc_username"]
    bmc_password=data["bmc_password"]

    return bmc_user, bmc_password


def parse_configuration_data_servers(data) -> dict[str, dict[str, str]]:
    data = {}

    for docu_file_name in glob.glob(f"{get_server_documentation_dir()}/Supermicro_*.md"):
        m = re.match(r".*/(.+)_(..+).md", docu_file_name)
        if not m:
            LOGGER.error("Unable to parse vendor and machine type from filename")
            sys.exit(1)
        machine_vendor = m.group(1)
        machine_type = m.group(2)

        LOGGER.debug(f"loading data from: {docu_file_name}")
        interfaces: list[dict[str,str]] = []
        with open(docu_file_name, 'r') as file:
            for line in file.readlines():
                m = re.fullmatch(r".*\s+NIC:\s+([a-z0-9]+?)\s*/\s* ASN:\s*(\d+)([\s].*|)", line.strip())
                if m:
                    interfaces.append( { "name": m.group(1), "remote_as": m.group(2) } )

                m = re.fullmatch(
                    r"\|\s*(?P<name>[a-z0-9-]+?)\s*\|"
                    r"\s*(?P<serial>[\da-zA-Z-]+?)\s*"
                    r"\|.+"
                    r"\|\s*(?P<bmc_ip_v4>\d+\.\d+\.\d+\.\d+?)\s*"
                    r"\|.+"
                    r"\|\s*(?P<bmc_mac>[a-f0-9:]+)\s*"
                    r"\|\s*(?P<asn>\d+|NONE)\s*"
                    r"\|\s*(?P<node_ip_v4>\d+\.\d+\.\d+\.\d+?)\s*"
                    r"\|\s*(?P<node_ip_v6>(?:[a-f0-9]{1,4}:){7}[a-f0-9]{1,4})\s*"
                    r"\|.*",
                    line.strip())
                if m:
                    data[m.group("name")] = m.groupdict()
                    data[m.group("name")]["bmc_password"], data[m.group("name")]["bmc_username"] = \
                        get_bmc_login_data(m.group("name"))
                    data[m.group("name")]["device_model"] = machine_type
                    data[m.group("name")]["device_vendor"] = machine_vendor
                    if len(interfaces) == 0:
                        raise RuntimeError("No interfaces found")
                    data[m.group("name")]["interfaces"] = sorted(interfaces, key=lambda x: x['name'])
                    for field in CONFIG_FIELDS_SERVERS:
                        if field not in data[m.group("name")]:
                            LOGGER.error(f"field not in line : >>{line.strip()}<<")

    return data


def get_unique_servers(host_list: list[str], full: bool, filter_hosts: str | None = None) -> list[str]:
    return get_unique("servers", full, host_list, filter_hosts)
