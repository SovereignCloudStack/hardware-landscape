import glob
import logging
import re
import sys

from .global_helpers import get_basedir
from .helpers import get_unique

LOGGER = logging.getLogger()

CONFIG_FIELDS_SWITCHES = ["name", "serial", "bmc_ip_v4", "bmc_username", "bmc_mac", "serial_device"]


def get_switch_documentation_dir() -> str:
    return f"{get_basedir()}/documentation/devices/network/"


def parse_configuration_data_switches(data) -> dict[str, dict[str, str]]:
    data = {}

    for docu_file_name in glob.glob(f"{get_switch_documentation_dir()}/Edgecore_*.md"):
        m = re.match(r".*/Edgecore_(..+).md", docu_file_name)
        if not m:
            LOGGER.error("Unable to parse machine type from filename")
            sys.exit(1)
        switch_type = m.group(1)

        LOGGER.debug(f"loading data from: {docu_file_name}")
        with open(docu_file_name, 'r') as file:
            for line in file.readlines():
                m = re.fullmatch(
                    r"\|\s*(?P<name>[a-z0-9-]+?)\s*\|"
                    r"\s*(?P<serial>[\da-zA-Z-]+?)\s*"
                    r"\|.+"
                    r"\|\s*(?P<bmc_ip_v4>\d+\.\d+\.\d+\.\d+?)\s*"
                    r"\|\s*(?P<bmc_mac>[a-f0-9:]+)\s*"
                    r"\|\s*(?P<serial_device>[A-Za-z0-9:]+)\s*"
                    r".*\|.*",
                    line.strip())
                if m:
                    data[m.group("name")] = m.groupdict()
                    data[m.group("name")]["device_model"] = switch_type
                    data[m.group("name")]["bmc_username"] = "admin"
                    for field in CONFIG_FIELDS_SWITCHES:
                        if field not in data[m.group("name")]:
                            LOGGER.error(f"field '{field}' not in line : >>{line.strip()}<<")

    return data


def get_unique_switches(host_list: list[str], full: bool, filter_hosts: str | None = None) -> list[str]:
    return get_unique("switches", full, host_list, filter_hosts)
