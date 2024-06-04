import functools
import glob
import logging
import os
import re
import sys
from typing import Tuple

import coloredlogs

LOGGER = logging.getLogger()

MGMT_GATEWAY_IP = "10.10.23.1"

def get_rundir() -> str:
    return os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/../")


def get_basedir() -> str:
    return get_rundir() + "/../../"


def get_server_documentation_dir() -> str:
    return f"{get_basedir()}/documentation/devices/servers/"


def get_ansible_host_inventory_dir() -> str:
    return f"{get_basedir()}/inventory/host_vars/"


def get_device_configurations_dir(device_type: str) -> str:
    return f"{get_basedir()}/device_configurations/{device_type}/"


def get_install_media_url(model: str):
    return f"http://10.10.23.254:8080/{model}.iso"


def setup_logging(log_level: str) -> Tuple[logging.Logger, str]:
    log_format_string = \
        '%(asctime)-10s - %(levelname)-7s - %(filename)s:%(lineno)d - %(name)s - %(message)s'
    logger = logging.getLogger()
    log_file = "STDOUT"
    logging.basicConfig(format=log_format_string,
                        level=log_level)

    coloredlogs.DEFAULT_FIELD_STYLES["levelname"] = {'bold': True, 'color': ''}
    coloredlogs.install(fmt=log_format_string, level=log_level)

    return logger, log_file


CONFIG_FIELDS = ['name', 'serial', 'bmc_ip_v4', 'bmc_mac', 'node_ip_v4', 'node_ip_v6', 'bmc_password', 'bmc_username',
                 'interfaces']


@functools.lru_cache
def parse_configuration_data() -> dict[str, dict[str, str]]:
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
        m = re.match(r".*/Supermicro_(..+).md", docu_file_name)
        if not m:
            LOGGER.error("Unable to parse machine type from filename")
            sys.exit(1)
        machine_type = m.group(1)

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
                    data[m.group("name")]["interfaces"] = sorted(interfaces)
                    for field in CONFIG_FIELDS:
                        if field not in data[m.group("name")]:
                            LOGGER.error(f"field not in line : >>{line.strip()}<<")

    return data


def get_unique_hosts(host_list: list[str]) -> list[str]:
    host_data = parse_configuration_data()
    result = set()
    for host in host_list:
        if host == "all":
            result = result | set(host_data.keys())
        else:
            result.add(host)
    return sorted(list(result))


def get_unique_hosts_full(host_list: list[str]) -> list[dict[str, str]]:
    result = []
    host_data = parse_configuration_data()
    for host in get_unique_hosts(host_list):
        result.append(host_data[host])
    return result


def regex_replace_in_file(file_path: str, replacements: list[tuple[str, str]]):
    modified_content = ""
    with open(file_path, 'r') as file:
        for line in file.readlines():
            changed_content = line
            for pattern, replacement in replacements:
                changed_content = re.sub(pattern, replacement, changed_content)
            modified_content += changed_content

    with open(file_path, 'w') as file:
        file.write(modified_content)
