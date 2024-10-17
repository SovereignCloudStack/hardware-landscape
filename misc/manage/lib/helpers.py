import argparse
import functools
import logging
import os
import re
import subprocess
import sys
from enum import Enum
from typing import Any

from jinja2 import FileSystemLoader, Environment, StrictUndefined

from .global_helpers import get_ansible_host_inventory_dir, get_basedir

LOGGER = logging.getLogger()


@functools.lru_cache
def parse_configuration_data() -> dict[str, dict[str, dict[str, str]]]:
    from .server_model import parse_configuration_data_servers
    from .switch_model import parse_configuration_data_switches
    data = {}
    data["servers"] = parse_configuration_data_servers(data)
    data["switches"] = parse_configuration_data_switches(data)
    return data


def get_unique(item_type: str, full: bool, host_list: list[str], filter_hosts: str | None = None) -> (
        list[str] | list[dict[str, str]]):
    host_data = parse_configuration_data()[item_type]
    result = set()
    for item_name in host_list:
        if item_name == "all":
            result = result | set(host_data.keys())
        else:
            result.add(item_name)

    if filter_hosts:
        new_result = set()
        key, value = filter_hosts.split("=")
        for item_name in result:
            if re.fullmatch(value.strip(), host_data[item_name][key.strip()]):
                new_result.add(item_name)
        result = new_result

    if full:
        result_full: list[dict[str, str]] = []
        for item_name in sorted(list(result)):
            result_full.append(host_data[item_name])
        return result_full
    else:
        return sorted(list(result))


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


class AnsibleInvertoryStrategy(str, Enum):
    REPLACE = 'replace'
    KEEP = 'keep'

    def __str__(self):
        return self.value


def ansible_inventory_strategy_type(arg_value: str):
    try:
        return AnsibleInvertoryStrategy[arg_value.upper()]
    except KeyError:
        raise argparse.ArgumentTypeError(
            f"Invalid option: '{arg_value.upper}'. Valid options are: "
            f"{', '.join(c.name.lower() for c in AnsibleInvertoryStrategy)}")


def template_ansible_config(host_list: list[str], item_type: str, strategy: AnsibleInvertoryStrategy):
    host_data = parse_configuration_data()[item_type]

    template_loader = FileSystemLoader(searchpath=get_ansible_host_inventory_dir())
    template_env = Environment(loader=template_loader, undefined=StrictUndefined)
    results_template = template_env.get_template(f"{item_type}-template.yml.j2")

    for host_name in host_list:
        LOGGER.info(f"host: {host_name}, strategy {strategy}")
        results_dir = f"{get_ansible_host_inventory_dir()}{host_name}/"
        os.makedirs(results_dir, exist_ok=True)

        results_filename = f"{results_dir}/01_base.yml"
        results_filename = os.path.realpath(results_filename)

        templated_string = results_template.render(host_data[host_name])

        if os.path.exists(results_filename):
            if strategy is AnsibleInvertoryStrategy.KEEP:
                LOGGER.warning(
                    f"Not templating {host_name} inventory file {results_filename}, ansible_inventory_update_strategy=keep")
                continue
            elif strategy is AnsibleInvertoryStrategy.REPLACE:
                LOGGER.warning(
                    f"Updating existing {host_name} file {results_filename}, ansible_inventory_update_strategy=update")
                with open(results_filename, 'w') as f_out:
                    f_out.write(templated_string)
            else:
                LOGGER.error(f"ansible_inventory_update_strategy invalid {strategy}")
                sys.exit(1)

        else:
            LOGGER.warning(f"Create a new file for {host_name}")
            with open(results_filename, mode="w", encoding="utf-8") as results:
                results.write(templated_string)

    subprocess.run(f"git --no-pager diff {get_ansible_host_inventory_dir()}", shell=True)


def create_configs(host_list: list[str], config_type: str):
    host_data = parse_configuration_data()[config_type]

    results_file = f"{get_basedir()}/config-snippets/ssh_config_scs_{config_type}"
    LOGGER.info(f"writing {results_file}")
    with open(results_file, 'w') as f_out:
        for host_name in host_list:
            LOGGER.info(f"** {host_name}")

            if 'bmc_ip_v4' in host_data[host_name]:
                f_out.write(f"Host scs-{host_name}-bmc\n")
                f_out.write(f"   Hostname {host_data[host_name]['bmc_ip_v4']}\n")

                if host_data[host_name]["device_vendor"] == "Supermicro":
                    # Workaround for crappy supermicro boxes
                    f_out.write("   HostKeyAlgorithms=+ssh-rsa\n")

                f_out.write(f"   User {host_data[host_name]['bmc_username']}\n")
                f_out.write("\n")

            if 'node_ip_v4' in host_data[host_name]:
                f_out.write(f"Host scs-{host_name}\n")
                f_out.write(f"   Hostname {host_data[host_name]['node_ip_v4']}\n")
                f_out.write("\n")


def filter_dict_keys(data: Any, allowed_keys_regex: list[str], key=None) -> dict | list | str | None:
    if isinstance(data, dict):
        tmp_dict = {}
        for k,v in data.items():
            result = filter_dict_keys(v, allowed_keys_regex, key=k)
            if result:
                tmp_dict[k] = result
        return tmp_dict
    elif isinstance(data, list):
        filtered_list = [filter_dict_keys(item, allowed_keys_regex) for item in data]
        return [item for item in filtered_list if item]
    else:
        for match_key_regex in allowed_keys_regex:
            if re.fullmatch(match_key_regex, key) and data is not None:
                return data
    return None

def print_all_dict_values(d: Any) -> int:
    count=0
    if isinstance(d, list):
        for value in d:
            count += print_all_dict_values(value)
    elif isinstance(d, dict):
        for value in d.values():
            count += print_all_dict_values(value)
    else:
        print(d)
        return 1
    return count
