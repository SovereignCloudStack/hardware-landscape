import glob
import logging
import xml
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from .helpers import get_basedir, parse_configuration_data

LOGGER = logging.getLogger()


def change_syslog(root: xml.etree.ElementTree):
    syslog_enable_element = root.find(".//SyslogEnable")
    syslog_enable_element.text = "Enable"

    syslog_server_element = root.find(".//SyslogServerIP")
    syslog_server_element.text = "10.10.23.1"

    syslog_port_element = root.find(".//SyslogPortNumber")
    syslog_port_element.text = "514"


def change_ntp(root: xml.etree.ElementTree):
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


def change_bmc_settings(root: xml.etree.ElementTree):
    element = root.find(".//WebSession/Configuration/Timeout")
    element.text = "0"


def change_virtual_media(root: xml.etree.ElementTree):
    element = root.find(".//VirtualMedia/Information/DeviceStatus")
    element.text = "Unmounted"

    element = root.find(".//VirtualMedia/Configuration/ShareHost")
    element.text = "10.10.23.1"

    element = root.find(".//VirtualMedia/Configuration/PathToImage")
    element.text = r'\media\ubuntu-autoinstall-osism-4.iso'

    element = root.find(".//VirtualMedia/Configuration/UserName")
    element.text = "osism"

    element = root.find(".//VirtualMedia/Configuration/UserPassword")
    element.text = "Oji2aet6"


def template_bmc_config(bmc_hosts: list[str]):
    host_data = parse_configuration_data()
    for hostname in bmc_hosts:
        matching_files = glob.glob(f"{get_basedir()}/config/*_{hostname}.xml")

        if len(matching_files) != 1:
            LOGGER.error(f"So such host {hostname}")
            break

        filename = matching_files[0]

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
        change_network(root_elem, hostname, host_data[hostname]["ip"])
        change_syslog(root_elem)
        change_ntp(root_elem)
        change_snmp(root_elem)
        change_virtual_media(root_elem)

        modified_xml_string = ElementTree.tostring(root_elem).decode()
        with open(filename, 'w') as file:
            file.write(modified_xml_string)
