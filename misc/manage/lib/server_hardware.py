import argparse
import glob
import logging
import os
import subprocess
import sys
import xml
from enum import Enum
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from .helpers import regex_replace_in_file, parse_configuration_data
from .global_helpers import get_rundir, get_basedir, get_device_configurations_dir
from .server_model import get_server_documentation_dir

LOGGER = logging.getLogger()


def change_syslog(root: xml.etree.ElementTree):
    syslog_enable_element = root.find(".//SyslogEnable")
    syslog_enable_element.text = "Enable"

    syslog_server_element = root.find(".//SyslogServerIP")
    syslog_server_element.text = "10.10.23.1"

    syslog_port_element = root.find(".//SyslogPortNumber")
    syslog_port_element.text = "514"


def change_ntp(root: xml.etree.ElementTree):

    if root.find(".//TimeUpdateMode"):
        element = root.find(".//TimeUpdateMode")
        element.text = "NTP"

        element = root.find(".//NTPPrimaryServer")
        element.text = "192.53.103.103"

        element = root.find(".//NTPSecondaryServer")
        element.text = "192.53.103.104"

        element = root.find(".//TimeZone")
        element.text = "+0000"

        element = root.find(".//DayLightSaving")
        element.text = "Disable"
    else:
        element = root.find(".//NTPEnable")
        element.text = "Enable"

        element = root.find(".//PrimaryNTPServer")
        element.text = "192.53.103.103"

        element = root.find(".//SecondaryNTPServer")
        element.text = "192.53.103.104"

        element = root.find(".//TimeZone")
        element.text = "(UTC+00:00) Coordinated Universal Time"

        element = root.find(".//AutoDSTEnabled")
        element.text = "Disable"


def change_snmp_community_config(elem: Element, mode: str, password: str):
    elem.set("Action", "Change")
    sub_element_access_mode = elem.find(".//AccessMode")
    sub_element_access_mode.text = mode
    sub_element_name = elem.find(".//Name")
    sub_element_name.text = mode
    sub_element_community_string = elem.find(".//CommunityString")
    sub_element_community_string.text = password


def create_snmp_community_config(mode: str, password: str, id: int):
    new_community_string = Element("CommunityStrings")
    new_community_string.set("Action", "Create")
    new_community_string.set("CommunityStringID", str(id))

    new_configuration_element = Element("Configuration")
    access_mode_element = Element("AccessMode")
    access_mode_element.text = mode
    new_configuration_element.append(access_mode_element)

    name_element = Element("Name")
    name_element.text = mode
    new_configuration_element.append(name_element)

    community_string_element = Element("CommunityString")
    community_string_element.text = password
    new_configuration_element.append(community_string_element)

    new_community_string.append(new_configuration_element)
    return new_community_string


def change_snmp(root: xml.etree.ElementTree):
    ro_community = "Eevaid7xoh4m"
    rw_community = "lohz3kaG5ted"

    element = root.find(".//ServiceEnabling/Configuration/SNMP")
    element.text = "Enable"
    if isinstance(root.find(".//Configuration/SNMPV2/ROCommunity"), Element):
        LOGGER.info("configure legacy snmp")
        element = root.find(".//SNMPV2/ROCommunity")
        element.text = ro_community
        element = root.find(".//SNMPV2/RWCommunity")
        element.text = rw_community
    else:
        LOGGER.info("configure latest snmp")
        element = root.find(".//SNMPV2/EnableSNMPv2c")
        element.text = "Enable"
        elements = root.find(".//SNMPV2")
        found_ids = []
        for element in elements:
            if element.tag == "CommunityStrings" and element.get("CommunityStringID") in ["1", "2"]:
                if element.get("CommunityStringID") == "1":
                    change_snmp_community_config(element, "ReadOnly", ro_community)
                elif element.get("CommunityStringID") == "2":
                    change_snmp_community_config(element, "ReadWrite", rw_community)
                else:
                    raise RuntimeError("Not implemented")
                found_ids.append(element.get("CommunityStringID"))

        if "1" not in found_ids:
            elements.append(create_snmp_community_config("ReadOnly", ro_community, 1))
        if "2" not in found_ids:
            elements.append(create_snmp_community_config("ReadWrite", rw_community, 2))


def change_network(root: xml.etree.ElementTree, hostname: str, ip: str):
    # element = root.find(".//IPProtocolStatus")
    # if element:
    #    element.text = "IPv4"

    element = root.find(".//HostName")
    element.text = hostname


    if root.find(".//IPv4/Configuration/IPSrc"):
        element = root.find(".//IPv4/Configuration/IPSrc")
        element.text = "Static"

        element = root.find(".//IPv4/Configuration/IPAddr")
        element.text = ip

        element = root.find(".//IPv4/Configuration/SubNetMask")
        element.text = "255.255.255.0"

        element = root.find(".//IPv4/Configuration/DefaultGateWayAddr")
        element.text = "10.10.23.1"

        element = root.find(".//IPv4/Configuration/DNSAddr")
        element.text = "8.8.8.8"
    else:
        element = root.find(".//IPv4/Configuration/DHCPEnabled")
        element.text = "Disable"

        element = root.find(".//IPv4/Configuration/Address")
        element.text = ip

        element = root.find(".//IPv4/Configuration/SubNetMask")
        element.text = "255.255.255.0"

        element = root.find(".//IPv4/Configuration/Gateway")
        element.text = "10.10.23.254"

        element = root.find(".//IPv4/Configuration/IPv4UseDNSServers")
        element.text = "Disable"

        element = root.find(".//IPv4/Configuration/IPv4StaticNameServer1")
        element.text = "8.8.8.8"


def change_bmc_settings(root: xml.etree.ElementTree):
    element = root.find(".//WebSession/Configuration/Timeout")
    element.text = "0"


# def change_virtual_media(root: xml.etree.ElementTree):
#     element = root.find(".//VirtualMedia/Information/DeviceStatus")
#     element.text = "Unmounted"
#
#     element = root.find(".//VirtualMedia/Configuration/ShareHost")
#     element.text = "10.10.23.254"
#
#     element = root.find(".//VirtualMedia/Configuration/PathToImage")
#     element.text = r'\media\ubuntu-autoinstall-osism-4.iso'
#
#     element = root.find(".//VirtualMedia/Configuration/UserName")
#     element.text = "osism"
#
#     element = root.find(".//VirtualMedia/Configuration/UserPassword")
#     element.text = "osism"


def template_bmc_config(bmc_hosts: list[str]):
    host_data = parse_configuration_data()["servers"]
    for hostname in bmc_hosts:
        print(get_server_documentation_dir())
        matching_files = glob.glob(f"{get_device_configurations_dir('server')}/*_{hostname}.xml")

        if len(matching_files) != 1:
            LOGGER.error(f"So such host {hostname}")
            break

        filename = os.path.realpath(matching_files[0])

        LOGGER.info(f"Processing {filename}")
        xml_string = None
        try:
            with open(filename, 'r') as file:
                xml_string = file.read()
        except Exception as e:
            LOGGER.error(f"FAILED: {e}")
            break

        root_elem = ElementTree.fromstring(xml_string)

        change_bmc_settings(root_elem)
        change_network(root_elem, hostname, host_data[hostname]["bmc_ip_v4"])
        change_syslog(root_elem)
        change_ntp(root_elem)
        change_snmp(root_elem)
        #change_virtual_media(root_elem)

        modified_xml_string = ElementTree.tostring(root_elem).decode()
        with open(filename, 'w') as file:
            file.write(modified_xml_string)


def execute_sum(data: dict[str, str], cmd: str):
    sum_log = "/tmp/sum"
    os.makedirs(sum_log, mode=0o777, exist_ok=True)
    sum_connect = \
        f"{get_rundir()}/venv/sum/sum --journal_path {sum_log} -i {data['bmc_ip_v4']} -u {data['bmc_username']} -p {data['bmc_password']}"
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


class CfgTypes(str, Enum):
    BIOS = 'bios'
    BMC = 'bmc'
    BOTH = "both"

    def __str__(self):
        return self.value


def configuration_type_strategy(arg_value: str):
    try:
        return CfgTypes[arg_value.upper()]
    except KeyError:
        raise argparse.ArgumentTypeError(
            f"Invalid option: '{arg_value.upper}'. Valid options are: "
            f"{', '.join(c.name.lower() for c in CfgTypes)}")

def configuration_type_strategy(arg_value: str):
    try:
        return CfgTypes[arg_value.upper()]
    except KeyError:
        raise argparse.ArgumentTypeError(
            f"Invalid option: '{arg_value.upper}'. Valid options are: "
            f"{', '.join(c.name.lower() for c in CfgTypes)}")


def backup_config(bmc_hosts: list[str], filetype: CfgTypes):
    host_data = parse_configuration_data()["servers"]
    for hostname in bmc_hosts:
        LOGGER.info(f"Processing server {hostname}")
        data = host_data[hostname]

        if data["device_model"] == "ARS-110M-NR":
            LOGGER.warning("Device dos not support backup/restore using sum")
            continue

        base_file_name = f"{get_device_configurations_dir('server')}{data['device_model']}_{hostname}"

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
