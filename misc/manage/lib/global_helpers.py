import glob
import logging
import os
import re
import subprocess
from datetime import datetime, timezone
from functools import cache
from typing import Tuple, Any

import coloredlogs
from ansible.parsing.vault import VaultSecret, VaultLib
import yaml
from mypy.types import names

from .constants import INSTALL_MEDIA_SERVER

def get_rundir() -> str:
    return os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/../")

def get_basedir() -> str:
    return get_rundir() + "/../../"


def get_ansible_host_inventory_dir() -> str:
    return f"{get_basedir()}/inventory/host_vars/"


def get_device_configurations_dir(device_type: str) -> str:
    return f"{get_basedir()}/device_configurations/{device_type}/"


def get_install_media_url(model: str):
    return f"{INSTALL_MEDIA_SERVER}/{model}.iso"


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

def get_ansible_secrets() -> dict[str,Any]:

    secrets = {}
    for file_name in (
            glob.glob(rf"{get_basedir()}/inventory/**/*.yml",recursive=True) +
            glob.glob(rf"{get_basedir()}/environments/**/*.yml",recursive=True)
        ):
        file_name = os.path.realpath(file_name)
        file_secrets = decrypt_vault_yaml_file(file_name)

        for name, value in file_secrets.items():
            secrets.setdefault(file_name, {})
            secrets[file_name][name] = value

    return secrets

def shorten_string(string: str, length: int = 300):
    return (string[:length] + ' ...') if len(string) > length else string


def get_string_with_formatted_timestamp(string: str):
    utc_dt = datetime.now(timezone.utc)
    iso_date = utc_dt.isoformat().replace(":", "-").replace(".", "_").replace("+", "-")
    return string % iso_date


def ask_for_confirmation(prompt="Are you sure?"):
    while True:
        response = input(prompt + " (y-es/n-o)").strip().lower()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("Please respond with 'yes' or 'no'.")


def generate_strings(expression: str):
    match = re.match(r'([^\{]*)\{(\d+)\.\.(\d+)\}([^\{]*)', expression)
    results = []
    if match:
        prefix, start, end, suffix = match.groups()
        start, end = int(start), int(end)
        results = [f"{prefix}{num}{suffix}" for num in range(start, end + 1)]
    else:
        results.append(expression)
    return results


@cache
def get_vault_pass() -> str:
    vault_pass_file = f"{get_basedir()}/secrets/vaultpass"
    if os.path.isfile(vault_pass_file):
        with open(vault_pass_file, 'r') as file:
            return file.readline().strip()
    else:
        result = subprocess.run("docker exec osism-ansible /ansible-vault.py".split(), capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            raise Exception(f"Command failed with error: {result.stderr}")


def decrypt_vault_yaml_file(file_path: str) -> dict[str, Any]:
    vault_secret = VaultSecret(get_vault_pass().encode())
    vault_lib = VaultLib(secrets=[('default', vault_secret)])
    with open(file_path, 'r') as vault_file:
        file_content = vault_file.read()

    if '$ANSIBLE_VAULT' not in file_content:
        return {}

    if '!vault' not in file_content:
        decrypted_content = vault_lib.decrypt(file_content)
        return yaml.safe_load(decrypted_content.decode())

    def vault_constructor(loader, node):
        value = loader.construct_scalar(node)
        return "vault: " + vault_lib.decrypt(value).decode()

    def filter_non_vault(data: dict[str, Any]) -> Any:
        if isinstance(data, dict):
            filtered_dict = {k: filter_non_vault(v) for k, v in data.items()}
            return {k: v for k, v in filtered_dict.items() if v}
        elif isinstance(data, list):
            filtered_list = [filter_non_vault(item) for item in data]
            return [item for item in filtered_list if item]
        elif isinstance(data, str):
            if data.startswith("vault: "):
                return data.removeprefix("vault: ")
        return None  # Return None for anything that doesn't match


    yaml.add_constructor('!vault', vault_constructor)
    decrypted_data = yaml.load(file_content, Loader=yaml.FullLoader)
    decrypted_data = filter_non_vault(decrypted_data)
    return decrypted_data
