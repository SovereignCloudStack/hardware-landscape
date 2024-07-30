#!/usr/bin/env python3
import pynetbox
import logging
import sys
import os
import argparse

from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~SITE~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@dataclass
class Site:
    name: str = "ST01"
    slug: str = "st01"
    status: str = "active"
    region: int = None
    tenant: int = None
    facility: str = "st01"
    asn: int = None
    physical_address: str = "1234 Street, City, Country, Earth"
    latitude: float = None
    longitude: float = None
    description: str = "ST01 site"
    comments: str = "ST01 site"

    @staticmethod
    def resource() -> str:
        return "sites"


# ~~~~~~~~~~~~~~~~~~~~~~~~~~RACK~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@dataclass
class Rack:
    site: str
    name: str = "Landscape"
    site_slug: str = "st01"
    status: str = "active"
    u_height: int = 47
    role: int = None
    type: str = "2-post-frame"
    width: str = "19"
    desc_units: bool = False
    outer_width: int = 600
    outer_depth: int = 800
    outer_unit: str = "mm"

    @staticmethod
    def resource() -> str:
        return "racks"


# ~~~~~~~~~~~~~~~~~~~~~~~~~~PLATFORM~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@dataclass
class Platform:
    name: str = "SONiC"
    slug: str = "sonic"
    description: str = ""

    @staticmethod
    def resource() -> str:
        return "platforms"


# ~~~~~~~~~~~~~~~~~~~~~~~~~~MANUFACTURER~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@dataclass
class Manufacturer:
    name: str = "Edgecore"
    slug: str = "edgecore"
    description: str = ""

    @staticmethod
    def resource() -> str:
        return "manufacturers"


# ~~~~~~~~~~~~~~~~~~~~~~~~~~DEVICE ROLE~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@dataclass
class DeviceRole:
    name: str
    slug: str
    color: str = "#000000"  # Default color (black) for the role

    @staticmethod
    def resource() -> str:
        return "device_roles"


# ~~~~~~~~~~~~~~~~~~~~~~~~~~CUSTOM FIELD~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@dataclass
class CustomField:
    name: str
    type: str = "text"
    object_types: tuple = ("dcim.interface",)
    description: str = "Custom field"

    @staticmethod
    def resource() -> str:
        return "custom_fields"


# ~~~~~~~~~~~~~~~~~~~~~~~~~~CUSTOM FIELD~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@dataclass
class ConfigTemplate:
    name: str
    template_code: str

    @staticmethod
    def resource() -> str:
        return "config_templates"


def create_or_update_dcim(nb: pynetbox.api, resource: str, params: object):
    try:
        resource_obj = getattr(nb.dcim, resource)
        # TODO: Rack has exception to GET the resource, try to prettyfy this
        if resource == "racks":
            existing_obj = resource_obj.get(site_id=params.site, name=params.name)
        else:
            existing_obj = resource_obj.get(slug=params.slug)

        if existing_obj:
            logger.info(f"{resource.capitalize()} already exists: {params.name}, updating it.")
            existing_obj.update(asdict(params))
            logger.info(f"{resource.capitalize()} updated successfully: {params.name}")
            return existing_obj

        new_obj = resource_obj.create(asdict(params))
        logger.info(f"{resource.capitalize()} created successfully: {new_obj.name}")
        return new_obj

    except pynetbox.RequestError as e:
        logger.error(f"{resource.capitalize()} creation or update failed: {e}")
        sys.exit(1)


def create_or_update_extras(nb: pynetbox.api, resource: str, params: object):
    try:
        resource_obj = getattr(nb.extras, resource)
        existing_obj = resource_obj.filter(name=params.name)

        if existing_obj:
            logger.info(f"{resource.capitalize()} already exists: {params.name}, updating it.")
            existing_obj.update(**asdict(params))
            logger.info(f"{resource.capitalize()} updated successfully: {params.name}")
            return existing_obj

        new_obj = resource_obj.create(asdict(params))
        logger.info(f"{resource.capitalize()} created successfully: {new_obj.name}")
        return new_obj

    except pynetbox.RequestError as e:
        logger.error(f"{resource.capitalize()} creation or update failed: {e}")
        sys.exit(1)


def environ_or_required(key):
    return (
        {"default": os.environ.get(key)} if os.environ.get(key)
        else {"required": True}
    )


parser = argparse.ArgumentParser(description="Bootstrap NetBox.")
parser.add_argument('--url', **environ_or_required('NETBOX_URL'), help="NetBox instance URL")
parser.add_argument('--token',  **environ_or_required('NETBOX_TOKEN'), help="NetBox API token")


if __name__ == "__main__":
    args = parser.parse_args()
    nb = pynetbox.api(args.url, token=args.token)
    # Add or update site
    site = create_or_update_dcim(nb, Site.resource(), Site())
    # Add or update rack
    rack_params = Rack(site=site.id)
    rack = create_or_update_dcim(nb, Rack.resource(), rack_params)
    # Add or update device roles
    for device_role in [
        DeviceRole(name="ManagementRouter", slug="management-router", color="ff0000"),
        DeviceRole(name="SpineRouter", slug="spine-router", color="00ff00"),
        DeviceRole(name="LeafRouter", slug="leaf-router", color="0000ff")
    ]:
        create_or_update_dcim(nb, device_role.resource(), device_role)
    # Add or update platform
    platform = create_or_update_dcim(nb, Platform.resource(), Platform())
    # Add or update manufacturer
    manufacturer = create_or_update_dcim(nb, Manufacturer.resource(), Manufacturer())
    # Add or update custom fields
    for custom_field in [
        CustomField(name="lanes", description="Custom field for lanes"),
        CustomField(name="alias", description="Custom field for aliases"),
        CustomField(name="autoneg", description="Custom field for autoneg"),
        CustomField(name="index", description="Custom field for indexes"),
    ]:
        create_or_update_extras(nb, custom_field.resource(), custom_field)

    create_or_update_extras(nb, ConfigTemplate.resource(), ConfigTemplate(
        name="test",
        template_code="{}"
    ))
