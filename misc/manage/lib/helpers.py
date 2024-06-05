import functools
import logging
import re


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
