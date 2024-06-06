import logging
import os
import subprocess
import sys
from enum import Enum

import yaml
from jinja2 import FileSystemLoader, Environment, StrictUndefined

from .global_helpers import get_device_configurations_dir, get_ansible_host_inventory_dir
from .helpers import parse_configuration_data, regex_replace_in_file

LOGGER = logging.getLogger()


class CfgTypes(str, Enum):
    main = 'main'
    frr = 'frr'
    both = "both"

def execute_sum(data: dict[str, str], cmd: str):
    sum_connect = \
        f"{get_rundir()}/venv/sum/sum -i {data['bmc_ip_v4']} -u {data['bmc_username']} -p {data['bmc_password']}"
    command = f"{sum_connect} {cmd}"
    LOGGER.info("EXEC: >>>%s<<<", command.replace(data["bmc_password"], "REDACTED"))

    p = subprocess.run(command, capture_output=True, shell=True, text=True)

    print("stdout: >>>%s<<<" % p.stdout.replace(data["bmc_password"], "REDACTED"))
    print("stderr: >>>%s<<<" % p.stderr.replace(data["bmc_password"], "REDACTED"))

    if p.returncode == 0:
        LOGGER.info(
            "SUCCESS - STDOUT: >>>%s<<<, STDERR: >>>%s<<<" % (
                p.stdout.replace(data["bmc_password"], "REDACTED"),
                p.stderr.replace(data["bmc_password"], "REDACTED")
            )
        )
    else:
        LOGGER.error("ERROR[%s] - STDOUT: >>>%s<<<, STDERR: >>>%s<<<" %
                     (
                         p.returncode,
                         p.stdout.replace(data["bmc_password"], "REDACTED"),
                         p.stderr.replace(data["bmc_password"], "REDACTED")
                     )
                     )
        sys.exit(1)



def backup_config(bmc_hosts: list[str], filetype: CfgTypes):
    host_data = parse_configuration_data()["servers"]
    for hostname in bmc_hosts:
        LOGGER.info(f"Processing server {hostname}")
        data = host_data[hostname]

        if data["device_model"] == "ARS-110M-NR":
            LOGGER.warning("Device dos not support backup/restore using sum")
            continue

        base_file_name = f"{get_device_configurations_dir('network')}{data['device_model']}_{hostname}"

        replacements: list[tuple[str, str]] = [
            tuple((r"File generated at ....-..-.._..:..:..", r"File generated at UNIFIED")),
            tuple((r"<DateTimeValue>..+</DateTimeValue>", r"<DateTimeValue>2024/1/1 11:11</DateTimeValue>"))
        ]

        if filetype in ["bios", "both"]:
            execute_sum(data, f"-c GetCurrentBiosCfg --file {base_file_name}.cfg --overwrite")
            regex_replace_in_file(f"{base_file_name}.cfg", replacements)
        if filetype in ["bmc", "both"]:
            execute_sum(data, f"-c GetBmcCfg --file {base_file_name}.xml --overwrite")
            regex_replace_in_file(f"{base_file_name}.xml", replacements)


def restore_config(bmc_hosts: list[str], filetype: CfgTypes):
    host_data = parse_configuration_data()["servers"]
    for hostname in bmc_hosts:
        LOGGER.info(f"Processing server {hostname}")
        data = host_data[hostname]
        if data["device_model"] == "ARS-110M-NR":
            LOGGER.warning("Device dos not support backup/restore using sum")
            continue

        base_file_name = f"{get_device_configurations_dir('server')}{data['device_model']}_{hostname}"
        if filetype in ["bios", "both"]:
            execute_sum(data, f"-c ChangeBiosCfg --file {base_file_name}.cfg")
        if filetype in ["bmc", "both"]:
            execute_sum(data, f"-c ChangeBmcCfg --file {base_file_name}.xml")
