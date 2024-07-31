#!/usr/bin/env python3
"""
NetBox init script

This script is used to bootstrap a NetBox instance by creating or updating various netbox
resources, see NB_API_MODEL_MAP.

Disclaimer: Script has not been tested with all Netbox objects defined NB_API_MODEL_MAP, hence some mey not work,
and the script needs to be fixed accordingly.

Basic Usage:
1. Ensure you have the necessary dependencies installed:
    pip install pynetbox pyyaml

2. Prepare a configuration files (e.g., data.yml, data2.yml) with the desired resources.

3. Run the script with the following command:
    ./netbox_init.py --api-url <NETBOX_URL> --api-token <NETBOX_TOKEN>  --data-file <DATA_FILE> --data-file <DATA_FILE>

Example data file (data.yml):
----------------------------------------
sites:
  - name: "ST01"
    slug: "st01"
    status: "active"
    physical_address: "1234 Street, City, Country, Earth"
    description: "ST01 site"

racks:
  - site:
      name: "ST01"
      slug: "st01"
    name: "Landscape"
    status: "active"
    u_height: 47
    type: "2-post-frame"
    width: "19"
    desc_units: false
    outer_width: 600
    outer_depth: 800
    outer_unit: "mm"

platforms:
  - name: "SONiC"
    slug: "sonic"
----------------------------------------
"""
from typing import List

import pynetbox
import logging
import sys
import os
import argparse
import yaml

from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NetboxApp(Enum):
    DCIM = "dcim"
    EXTRAS = "extras"
    IPAM = "ipam"


@dataclass
class Meta:
    app: NetboxApp
    required: List[str]
    filer: List[str]


META = {
    "tags": Meta(
        app=NetboxApp.EXTRAS, required=["name", "slug", "color"], filer=["slug"]
    ),
    "regions": Meta(app=NetboxApp.DCIM, required=["name", "slug"], filer=["slug"]),
    "sites": Meta(
        app=NetboxApp.DCIM, required=["name", "slug", "status"], filer=["slug"]
    ),
    "locations": Meta(
        app=NetboxApp.DCIM, required=["site", "name", "slug", "status"], filer=["slug"]
    ),
    "rack-roles": Meta(
        app=NetboxApp.DCIM, required=["name", "slug", "color"], filer=["slug"]
    ),
    "racks": Meta(
        app=NetboxApp.DCIM,
        required=["site", "name", "status", "width", "u_height"],
        filer=["name", "location", "site"],
    ),
    "manufacturers": Meta(
        app=NetboxApp.DCIM, required=["name", "slug"], filer=["slug"]
    ),
    "platforms": Meta(app=NetboxApp.DCIM, required=["name", "slug"], filer=["slug"]),
    "device-roles": Meta(
        app=NetboxApp.DCIM, required=["name", "slug", "color"], filer=["slug"]
    ),
    "custom-fields": Meta(
        app=NetboxApp.EXTRAS, required=["name", "type", "object_types"], filer=["name"]
    ),
    "config-templates": Meta(
        app=NetboxApp.EXTRAS, required=["name", "template_code"], filer=["name"]
    ),
    "devices": Meta(
        app=NetboxApp.DCIM,
        required=["role", "device_type", "status", "site", "name"],
        filer=["name"],
    ),
    "ip-addresses": Meta(
        app=NetboxApp.IPAM, required=["address", "status"], filer=["address", "device"]
    ),
}


def load_data(file_path):
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


def get_model_id(nb: pynetbox.api, nb_model: str, params: dict):
    try:
        nb_meta = META[nb_model]
    except KeyError:
        logger.error(f"{nb_model.capitalize()} is not implemented")
        sys.exit(1)

    nb_filter = {key: params[key] for key in nb_meta.filer}

    try:
        app_obj = getattr(nb, nb_meta.app.value)
        model_obj = getattr(app_obj, nb_model)
        model = model_obj.get(**nb_filter)

        if model:
            return model.id

        logger.error(f"{nb_model.capitalize()} with {nb_filter} not found.")
        sys.exit(1)

    except pynetbox.RequestError as e:
        logger.error(f"Failed to get {nb_model.capitalize()}: {e}")
        sys.exit(1)


def mangle_ip_addresses(nb: pynetbox.api, params: dict):

    if "device" in params and "interface" in params:
        params.update(
            {
                "assigned_object_type": "dcim.interface",
                "assigned_object_id": get_model_id(
                    nb, "devices", {"name": params["device"]}
                ),
            }
        )
        return

    logger.error(f"Unsupported ip-address values")
    sys.exit(1)


def create_or_update(nb: pynetbox.api, nb_model: str, params: dict):
    try:
        nb_meta = META[nb_model]
    except KeyError:
        logger.error(f"{nb_model.capitalize()} is not implemented")
        sys.exit(1)

    try:
        {key: params[key] for key in nb_meta.required}
    except KeyError:
        logger.error(f"{nb_model.capitalize()} missing required parameter")
        sys.exit(1)

    nb_filter = {}
    for key in nb_meta.filer:
        try:
            nb_filter_value = params[key]
        except KeyError:
            logger.error(f"{nb_model.capitalize()} missing filer parameter")
            sys.exit(1)

        if isinstance(nb_filter_value, str) or isinstance(nb_filter_value, bool):
            nb_filter.update({key: nb_filter_value})
        else:
            # FIXME: improve this naive implementation
            nb_filter.update({key: nb_filter_value["slug"]})

    if nb_model == "ip-addresses" and "device" in params:
        mangle_ip_addresses(nb, params)

    try:
        app_obj = getattr(nb, nb_meta.app.value)
        model_obj = getattr(app_obj, nb_model)
        existing_resource = model_obj.get(**nb_filter)

        if existing_resource:
            logger.info(
                f"{nb_model.capitalize()} already exists: {nb_filter}, updating it."
            )
            existing_resource.update(params)
            logger.info(f"{nb_model.capitalize()} updated successfully: {nb_filter}")
            return existing_resource

        new_resource = model_obj.create(params)
        logger.info(f"{nb_model.capitalize()} created successfully: {nb_filter}")
        return new_resource

    except pynetbox.RequestError as e:
        logger.error(f"{nb_model.capitalize()} creation or update failed: {e}")
        sys.exit(1)


def environ_or_required(key):
    return (
        {"default": os.environ.get(key)} if os.environ.get(key) else {"required": True}
    )


parser = argparse.ArgumentParser(description="Bootstrap NetBox.")
parser.add_argument(
    "--api-url", "-u", **environ_or_required("NETBOX_URL"), help="NetBox instance URL"
)
parser.add_argument(
    "--api-token", "-t", **environ_or_required("NETBOX_TOKEN"), help="NetBox API token"
)
parser.add_argument(
    "--data-file",
    "-d",
    action="append",
    required=True,
    help="Path to the netbox data file",
)


if __name__ == "__main__":
    args = parser.parse_args()
    nb = pynetbox.api(args.api_url, token=args.api_token)

    for data_file in args.data_file:
        data = load_data(data_file)
        for nb_model, items in data.items():
            for params in items:
                create_or_update(nb, nb_model, params)
