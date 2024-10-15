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


def decrypt_vault_file(file_path: str):
    vault_secret = VaultSecret(get_vault_pass().encode())
    vault_lib = VaultLib(secrets=[('default', vault_secret)])
    with open(file_path, 'r') as vault_file:
        encrypted_content = vault_file.read()

    decrypted_content = vault_lib.decrypt(encrypted_content)
    return decrypted_content.decode()

def decrypt_vault_yaml_file(file_path: str) -> dict[str,Any]:
    decrypted_content = decrypt_vault_file(file_path)
    return yaml.safe_load(decrypted_content)
