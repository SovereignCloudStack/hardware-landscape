import json
import logging
import os
import subprocess
import sys
from enum import Enum

import yaml
from jinja2 import FileSystemLoader, Environment, StrictUndefined

from .global_helpers import get_device_configurations_dir, get_ansible_host_inventory_dir, shorten_string, \
    get_string_with_formatted_timestamp, ask_for_confirmation, get_basedir
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
        base_file_name = f"{get_device_configurations_dir('network')}{data['device_model']}_{hostname}"

        if filetype in ["frr", "both"]:
            backup_file = get_string_with_formatted_timestamp("config_db_%s_frr_backup.conf")

            subprocess.run(f"scp {base_file_name}_frr.conf {data['bmc_username']}@{data['bmc_ip_v4']}:frr_restore.conf",
                           check=True,
                           shell=True,
                           )

            command = f"sudo vtysh -c 'show running-config' > {backup_file} && " + \
                      "sudo cp frr_restore.conf /etc/sonic/frr/frr.conf && " + \
                      "sudo chown 300:300 /etc/sonic/frr/frr.conf && docker restart bgp"

            execute_switch_commands(host_data[hostname], command)

        if filetype in ["main", "both"]:
            backup_file = get_string_with_formatted_timestamp("config_db_%s_main_backup.json")

            subprocess.run(
                f"scp {base_file_name}_main.json {data['bmc_username']}@{data['bmc_ip_v4']}:config_db_restore.json",
                check=True,
                shell=True,
            )

            command = f"sudo config save {backup_file}.json -y && " + \
                      "sudo cp config_db_restore.json /etc/sonic/config_db.json && " + \
                      "sudo config reload -y"
            execute_switch_commands(host_data[hostname], command)

        if ask_for_confirmation("Do you want to reboot the device?"):
            subprocess.run(
                f"ssh {data['bmc_username']}@{data['bmc_ip_v4']} sudo reboot",
                check=True,
                shell=True,
            )


def create_configs(host_list: list[str]):
    host_data = parse_configuration_data()["switches"]

    results_file = f"{get_basedir()}/config-snippets/ssh_config_scs_switches"
    LOGGER.info(f"writing {results_file}")
    with open(results_file, 'w') as f_out:
        for host_name in host_list:
            LOGGER.info(f"** {host_name} / {host_data[host_name]['bmc_ip_v4']}")
            f_out.write(f"Host scs-bmc-{host_name}\n")
            f_out.write(f"   Hostname {host_data[host_name]['bmc_ip_v4']}\n")
            f_out.write(f"   User {host_data[host_name]['bmc_username']}\n")
            f_out.write(f"\n")

    results_file = f"{get_basedir()}/config-snippets/screenrc_config"
    LOGGER.info(f"writing {results_file}")
    with open(results_file, 'w') as f_out:
        for host_name in host_list:
            LOGGER.info(f"** {host_name} / {host_data[host_name]['serial_device']}")
            f_out.write(f"Host scs-bmc-{host_name}\n")
            f_out.write(f"   Hostname {host_data[host_name]['bmc_ip_v4']}\n")
            f_out.write(f"   User {host_data[host_name]['bmc_username']}\n")
            f_out.write(f"\n")

