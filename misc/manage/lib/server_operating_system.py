import json
import logging
import os.path
import socket
from time import sleep

import webbrowser

import requests
from requests.auth import HTTPBasicAuth
import sushy
from sushy import auth
from sushy.resources.manager.manager import Manager
import urllib3

from .global_helpers import get_ansible_host_inventory_dir, get_install_media_url
from jinja2 import Environment, FileSystemLoader, StrictUndefined
import yaml

from .helpers import parse_configuration_data

MAX_WAIT = 120
STEP_WAIT = 15

LOGGER = logging.getLogger()


def control_server(url: str, http_auth: HTTPBasicAuth, mode: str):
    LOGGER.info("Setting Power %s" % mode)

    result = requests.post(
        f"{url}/Systems/1/Actions/ComputerSystem.Reset",
        auth=http_auth,
        verify=False,
        data=json.dumps({"ResetType": mode}),
    )
    result.raise_for_status()
    LOGGER.info(f"RESULT: >>>{result}<<<")
    try:
        data = result.json()
        LOGGER.info(f"Result >>>{data}<<<")
    except:
        pass


def check_power_off(url: str, http_auth: HTTPBasicAuth):
    result = requests.get(f"{url}/Systems/1", auth=http_auth, verify=False)
    data = result.json()
    if data["PowerState"] == "Off":
        return True
    return False


def tcp_test_connect(host: str, port: int, timeout: float = 5):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        return True
    except socket.error as e:
        return False
    finally:
        sock.close()


def check_power_servers(host_list: list[str]):
    host_data = parse_configuration_data()["servers"]
    for host_name in host_list:
        (mgr_inst, http_auth, redfish_url) = _setup_bmc_connection(host_data[host_name])
        if check_power_off(redfish_url, http_auth):
            LOGGER.warning(f"Server {host_name} / {host_data[host_name]['node_ip_v4']} is powered OFF")
        else:
            if tcp_test_connect(host_data[host_name]['node_ip_v4'], 22, 0.5):
                reachable = "online (tcp 22/ssh)"
            else:
                reachable = "not reachable on tcp port 22/ssh"
            LOGGER.info(f"Server {host_name} / {host_data[host_name]['node_ip_v4']} is powered ON, {reachable}")


def wait_power_off(url: str, http_auth: HTTPBasicAuth):
    control_server(url, http_auth, "ForceOn")
    sleep(120)

    wait = 15
    while wait > 0:
        LOGGER.info("Waiting for power off")
        if check_power_off(url, http_auth):
            break
        wait -= 1
        sleep(60)

    if wait > 0:
        LOGGER.info("Power went off with wait = %d" % wait)
    else:
        LOGGER.error("Timeout waiting for power off")
        raise Exception


def _setup_bmc_connection(host_details: dict[str, str]):
    urllib3.disable_warnings()
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logger = logging.getLogger("sushy")
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())

    if host_details["device_model"].startswith("ARS"):
        # https://github.com/openbmc/docs/blob/master/REDFISH-cheatsheet.md
        raise RuntimeError("redfish not implemented")

    redfish_url = "https://%s/redfish/v1" % host_details["bmc_ip_v4"]

    basic_auth = auth.BasicAuth(username=host_details["bmc_username"], password=host_details["bmc_password"])
    http_auth = HTTPBasicAuth(host_details["bmc_username"], host_details["bmc_password"])

    s = sushy.Sushy(redfish_url, auth=basic_auth, verify=False)

    mgr_inst = s.get_manager()
    return mgr_inst, http_auth, redfish_url


def control_servers(host_list: list[str], mode="ForceOff"):
    host_data = parse_configuration_data()["servers"]
    for host_name in host_list:
        LOGGER.info(f"Invoking operation '{mode}' on {host_name}")
        (mgr_inst, http_auth, redfish_url) = _setup_bmc_connection(host_data[host_name])
        control_server(redfish_url, http_auth, mode)


def virtual_media_insert_new(media_url: str, mgr_inst: Manager):
    # Password is not critical
    # smbclient --max-protocol NT1 --user osism --password osism '\\10.10.23.1\media\'

    virtual_media_col = mgr_inst.virtual_media
    if len(virtual_media_col.members_identities) > 0:
        if virtual_media_col.redfish_version == "1.0.1":
            raise RuntimeError("This is redfish 1.0.1, currently unsupported")
        #    virtual_media_col.members_identities = ("/redfish/v1/Managers/1/VirtualMedia/1")
        for member_identity in virtual_media_col.members_identities:
            virtual_media_inst = virtual_media_col.get_member(member_identity)
            if virtual_media_inst.inserted:
                LOGGER.info(f"Ejecting old media {member_identity}")
                virtual_media_inst.eject_media()
            virtual_media_inst.refresh()

    virtual_media_inst = virtual_media_col.get_member(virtual_media_col.members_identities[0])
    LOGGER.info(f"Inserting new media {media_url}")
    virtual_media_inst.insert_media(media_url)

    for sys in mgr_inst.systems:
        LOGGER.info("Set CD as next boot device")
        sys.set_system_boot_source(
            target=sushy.BOOT_SOURCE_TARGET_CD,
            enabled=sushy.BOOT_SOURCE_ENABLED_ONCE
        )

    success = False
    for sec_wait in range(0, MAX_WAIT, STEP_WAIT):
        virtual_media_inst.refresh()
        if virtual_media_inst.inserted:
            success = True
            break
        LOGGER.info(f"Waiting {STEP_WAIT} seconds for inserted media ({sec_wait}s/{MAX_WAIT}s) ")
        sleep(STEP_WAIT)

    if not success:
        raise RuntimeError(f"Unable to insert virtual media {media_url}")
    return virtual_media_inst


def install_server(host_list: list[str], media_url: str, open: bool):
    host_data = parse_configuration_data()["servers"]

    for host_name in host_list:
        (mgr_inst, http_auth, redfish_url) = _setup_bmc_connection(host_data[host_name])

        server_ident = f"{host_name} / {host_data[host_name]['bmc_ip_v4']}"

        if open:
            open_servers([host_name])

        if not check_power_off(redfish_url, http_auth):
            LOGGER.error(f"** {server_ident} - Power is not OFF for host, cowardly refusing to continue")
            exit(1)

        LOGGER.info(f"** {server_ident} - Starting phase 1 of the installation")

        if media_url == "auto":
            media_url = get_install_media_url(host_data[host_name]["device_model"])

        virtual_media_inst = virtual_media_insert_new(media_url, mgr_inst)

        control_server(redfish_url, http_auth, "ForceOn")
        sleep(30)
        wait_power_off(redfish_url, http_auth)
        virtual_media_inst.eject_media()

        LOGGER.info(f"** {server_ident} - Starting phase 2 of the installation")
        control_server(redfish_url, http_auth, "ForceOn")
        wait_power_off(redfish_url, http_auth)
        LOGGER.info(f"** {server_ident} - Installation finished, starting server now")
        control_server(redfish_url, http_auth, "ForceOn")


def open_servers(host_list: list[str]):
    host_data = parse_configuration_data()["servers"]

    for host_name in host_list:
        LOGGER.info(f"** {host_name} / {host_data[host_name]['bmc_ip_v4']}")
        LOGGER.info(f"Login: {host_data[host_name]['bmc_username']}")
        LOGGER.info(f"Password: {host_data[host_name]['bmc_password']}")
        # Supermciro BMC does not work with other browsers like "firefox"
        webbrowser.get("google-chrome").open(f"https://{host_data[host_name]['bmc_ip_v4']}", new=2)


def template_ansible_config(host_list: list[str]):
    host_data = parse_configuration_data()["servers"]

    template_loader = FileSystemLoader(searchpath=get_ansible_host_inventory_dir())
    template_env = Environment(loader=template_loader, undefined=StrictUndefined)
    results_template = template_env.get_template("server-template.yml.j2")

    for host_name in host_list:
        results_filename = f"{get_ansible_host_inventory_dir()}{host_name}.yml"

        LOGGER.info(f"rendering file : {results_filename}")
        templated_string = results_template.render(host_data[host_name])
        templated_data = yaml.safe_load(templated_string)

        if os.path.exists(results_filename):
            with open(results_filename, 'r') as file:
                existing_config = yaml.safe_load(file)
                if existing_config.get("inventory_generate_strategy", "replace") == "keep":
                    LOGGER.warning(f"Not templating {host_name} inventory file, inventory_generate_strategy=keep")
                    continue
                if existing_config.get("inventory_generate_strategy", "replace") == "update":
                    LOGGER.warning(f"Updating existing {host_name} inventory file, inventory_generate_strategy=update")
                    # TODO: do a better merge strategy without messing up the formatting
                    merged_data = {**templated_data, **existing_config}
                    with open(results_filename, 'w') as f_out:
                        yaml.dump(merged_data, f_out)
        else:
            with open(results_filename, mode="w", encoding="utf-8") as results:
                results.write(templated_string)
