import glob
import logging
import os
import re
import sys

from .global_helpers import get_basedir
from .helpers import get_unique

LOGGER = logging.getLogger()

CONFIG_FIELDS_SERVERS = ['name', 'serial', 'bmc_ip_v4', 'bmc_mac', 'node_ip_v4',
                         'node_ip_v6', 'bmc_password', 'bmc_username', 'interfaces']

def get_server_documentation_dir() -> str:
    return f"{get_basedir()}/documentation/devices/servers/"


def parse_configuration_data_servers(data) -> dict[str, dict[str, str]]:
    data = {}
    password_dict = {}
    server_passwords_file = f"{get_basedir()}/secrets/server.passwords"
    if not os.path.isfile(server_passwords_file):
        LOGGER.error(f"Unable to open the server passwords file {server_passwords_file}")
        sys.exit(1)
    with open(server_passwords_file, 'r') as file:
        LOGGER.debug("Reading ")
        for line in file.readlines():
            m = re.fullmatch(r"(?P<username>[a-z0-9A-Z]+)\s+(?P<mac>[a-f0-9:]+)\s+(?P<password>[A-Z-a-z0-9]+)",
                             line.strip())
            if m:
                password_dict[m.group("mac")] = {"username": m.group("username"), "password": m.group("password")}
    for docu_file_name in glob.glob(f"{get_server_documentation_dir()}/Supermicro_*.md"):
        m = re.match(r".*/(.+)_(..+).md", docu_file_name)
        if not m:
            LOGGER.error("Unable to parse vendor and machine type from filename")
            sys.exit(1)
        machine_vendor = m.group(1)
        machine_type = m.group(2)

        LOGGER.debug(f"loading data from: {docu_file_name}")
        interfaces: list[str] = []
        with open(docu_file_name, 'r') as file:
            for line in file.readlines():
                m = re.fullmatch(r".*\s+NIC:\s+([a-z0-9]+?)([\s].*|)", line.strip())
                if m:
                    interfaces.append(m.group(1))

                m = re.fullmatch(
                    r"\|\s*(?P<name>[a-z0-9-]+?)\s*\|"
                    r"\s*(?P<serial>[\da-zA-Z-]+?)\s*"
                    r"\|.+"
                    r"\|\s*(?P<bmc_ip_v4>\d+\.\d+\.\d+\.\d+?)\s*"
                    r"\|.+"
                    r"\|\s*(?P<bmc_mac>[a-f0-9:]+)\s*"
                    r"\|\s*(?P<node_ip_v4>\d+\.\d+\.\d+\.\d+?)\s*"
                    r"\|\s*(?P<node_ip_v6>(?:[a-f0-9]{1,4}:){7}[a-f0-9]{1,4})\s*"
                    r"\|.*",
                    line.strip())
                if m:
                    data[m.group("name")] = m.groupdict()
                    data[m.group("name")]["bmc_password"] = password_dict[m.group("bmc_mac")]["password"]
                    data[m.group("name")]["bmc_username"] = password_dict[m.group("bmc_mac")]["username"]
                    data[m.group("name")]["device_model"] = machine_type
                    data[m.group("name")]["device_vendor"] = machine_vendor
                    data[m.group("name")]["interfaces"] = sorted(interfaces)
                    for field in CONFIG_FIELDS_SERVERS:
                        if field not in data[m.group("name")]:
                            LOGGER.error(f"field not in line : >>{line.strip()}<<")

    return data


def get_unique_servers(host_list: list[str], full: bool, filter_hosts: str | None = None) -> list[str]:
    return get_unique("servers", full, host_list, filter_hosts)


