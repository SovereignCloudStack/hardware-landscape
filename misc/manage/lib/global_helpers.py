import logging
import os
from datetime import datetime, timezone
from typing import Tuple

import coloredlogs

MGMT_GATEWAY_IP = "10.10.23.1"


def get_rundir() -> str:
    return os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/../")


def get_basedir() -> str:
    return get_rundir() + "/../../"


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


def shorten_string(string: str, length: int = 300):
    return (string[:length] + ' ...') if len(string) > length else string


def get_string_with_formatted_timestamp(string: str):
    utc_dt = datetime.now(timezone.utc)
    iso_date = utc_dt.isoformat().replace(":","-").replace(".","_").replace("+","-")
    return string % iso_date


def ask_for_confirmation(prompt="Are you sure?"):
    while True:
        response = input(prompt+" (y-es/n-o)").strip().lower()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("Please respond with 'yes' or 'no'.")