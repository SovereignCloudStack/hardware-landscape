import json
import logging
import os
import subprocess
import sys
from enum import Enum

import yaml
from jinja2 import FileSystemLoader, Environment, StrictUndefined

from .global_helpers import get_device_configurations_dir, get_ansible_host_inventory_dir, shorten_string
from .helpers import parse_configuration_data, regex_replace_in_file

LOGGER = logging.getLogger()


class CfgTypes(str, Enum):
    main = 'main'
    frr = 'frr'
    both = "both"


def execute_switch_commands(data: dict[str, str], cmd: str) -> str:
    ssh_connect = f"ssh {data['bmc_username']}@{data['bmc_ip_v4']}"
    command = f"{ssh_connect} \"{cmd}\""
    LOGGER.info("EXEC: >>>%s<<<", command)

    p = subprocess.run(command, capture_output=True, shell=True, text=True)

    if p.returncode == 0:
        LOGGER.info(
            "SUCCESS - STDOUT: >>>%s<<<, STDERR: >>>%s<<<" % (
                shorten_string(p.stdout),
                shorten_string(p.stderr)
            )
        )
        return str(p.stdout)
    else:
        LOGGER.error("ERROR[%s] - STDOUT: >>>%s<<<, STDERR: >>>%s<<<" %
                     (
                         p.returncode,
                         p.stdout,
                         p.stderr
                     )
                     )
        sys.exit(1)


def backup_config(bmc_hosts: list[str], filetype: CfgTypes):
    host_data = parse_configuration_data()["switches"]
    for hostname in bmc_hosts:
        LOGGER.info(f"Processing switch {hostname}")
        data = host_data[hostname]

        if data["device_model"] == "ARS-110M-NR":
            LOGGER.warning("Device dos not support backup/restore using sum")
            continue

        base_file_name = f"{get_device_configurations_dir('network')}{data['device_model']}_{hostname}"

        if filetype in ["frr", "both"]:
            frr_backup = """sudo vtysh -c 'show running-config' > frr_backup.conf && cat frr_backup.conf"""
            result = execute_switch_commands(host_data[hostname], frr_backup)
            results_file = f"{base_file_name}_frr.conf"
            print(f"writing {results_file}")
            with open(results_file, 'w') as f_out:
                config_started = False
                for line in result.split("\n"):
                    if line.startswith("!"):
                        config_started = True
                    if config_started:
                        f_out.write(line)
                        
        if filetype in ["main", "both"]:
            frr_backup = """sudo config save config_db_backup.json -y >&2 && cat config_db_backup.json"""
            result = execute_switch_commands(host_data[hostname], frr_backup)
            json_data = json.loads(result)

            results_file = f"{base_file_name}_main.json"
            print(f"writing {results_file}")
            with open(results_file, 'w') as f_out:
                f_out.write(json.dumps(json_data, indent=2, sort_keys=True))


def restore_config(bmc_hosts: list[str], filetype: CfgTypes):
    host_data = parse_configuration_data()["switches"]
    for hostname in bmc_hosts:
        LOGGER.info(f"Processing switch {hostname}")
        data = host_data[hostname]
        # if data["device_model"] == "ARS-110M-NR":
        #     LOGGER.warning("Device dos not support backup/restore using sum")
        #     continue
        #
        # base_file_name = f"{get_device_configurations_dir('server')}{data['device_model']}_{hostname}"
        # if filetype in ["bios", "both"]:
        #     execute_sum(data, f"-c ChangeBiosCfg --file {base_file_name}.cfg")
        # if filetype in ["bmc", "both"]:
        #     execute_sum(data, f"-c ChangeBmcCfg --file {base_file_name}.xml")
