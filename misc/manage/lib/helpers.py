import functools
import logging
import os
import re
import subprocess
import sys
from enum import Enum

import yaml
from jinja2 import FileSystemLoader, Environment, StrictUndefined

from .global_helpers import get_ansible_host_inventory_dir

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
    update = 'update'
    keep = 'keep'


def template_ansible_config(host_list: list[str], item_type: str, strategy: AnsibleInvertoryStrategy):
    host_data = parse_configuration_data()[item_type]

    template_loader = FileSystemLoader(searchpath=get_ansible_host_inventory_dir())
    template_env = Environment(loader=template_loader, undefined=StrictUndefined)
    results_template = template_env.get_template(f"{item_type}-template.yml.j2")

    for host_name in host_list:
        results_filename = f"{get_ansible_host_inventory_dir()}{host_name}.yml"
        results_filename = os.path.realpath(results_filename)
        templated_string = results_template.render(host_data[host_name])

        if os.path.exists(results_filename):
            with open(results_filename, 'r') as file:
                if strategy:
                    if strategy == "keep":
                        LOGGER.warning(f"Not templating {host_name} inventory file {results_filename}, inventory_generate_strategy=keep")
                        continue
                    elif strategy == "update":
                        LOGGER.warning(f"Updating existing {host_name} file {results_filename}, inventory_generate_strategy=update")
                        with open(results_filename, 'w') as f_out:
                            f_out.write(templated_string)
                else:
                    LOGGER.error("inventory_generate_strategy not set")
                    sys.exit(1)

        else:
            LOGGER.warning(f"Create a new file for {host_name}")
            with open(results_filename, mode="w", encoding="utf-8") as results:
                results.write(templated_string)

    subprocess.run(f"git --no-pager diff {get_ansible_host_inventory_dir()}", shell=True)
