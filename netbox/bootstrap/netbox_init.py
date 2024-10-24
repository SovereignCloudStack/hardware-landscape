#!/usr/bin/env python3
"""
NetBox init script

This script is used to bootstrap a NetBox instance by creating or updating various netbox
resources, see META.

Basic Usage:
1. Ensure you have the necessary dependencies installed:
    pip install pynetbox pyyaml

2. Prepare a configuration files (e.g., data.yml, data2.yml) with the desired resources.

3. Run the script with the following command:
    ./netbox_init.py --api-url <NETBOX_URL> --api-token <NETBOX_TOKEN>  --data-file <DATA_FILE> --data-file <DATA_FILE>

Example data file (data.yml):
----------------------------------------
regions:
  - name: Europe
    slug: europe
  - name: Germany
    slug: germany
    parent:
      slug: europe
sites:
  - name: "ST01"
    slug: "st01"
    status: "active"
    facility: "st01"
    physical_address: "1234 Street, City, Country, Earth"
    description: "ST01 site"
    region:
      slug: germany
----------------------------------------
"""
import pynetbox
import logging
import sys
import os
import argparse
import yaml
import requests
import time
import glob

from collections.abc import Mapping
from typing import List
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
    CORE = "core"


@dataclass
class Meta:
    app: NetboxApp
    required: List[str]
    filer: List[str]


META = {
    "data-sources": Meta(
        app=NetboxApp.CORE, required=["name", "type", "source_url"], filer=["name"]
    ),
    "tags": Meta(
        app=NetboxApp.EXTRAS, required=["name", "slug", "color"], filer=["slug"]
    ),
    "custom-fields": Meta(
        app=NetboxApp.EXTRAS, required=["name", "type", "object_types"], filer=["name"]
    ),
    "config-templates": Meta(app=NetboxApp.EXTRAS, required=["name"], filer=["name"]),
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
    "devices": Meta(
        app=NetboxApp.DCIM,
        required=["role", "device_type", "status", "site", "name"],
        filer=["name"],
    ),
    "interfaces": Meta(
        app=NetboxApp.DCIM,
        required=["device", "name", "type"],
        filer=["name", "device"],
    ),
    "ip-addresses": Meta(
        app=NetboxApp.IPAM, required=["address", "status"], filer=["address"]
    ),
    "ip-ranges": Meta(
        app=NetboxApp.IPAM,
        required=["start_address", "end_address", "status"],
        filer=["start_address", "end_address"],
    ),
    "vlans": Meta(
        app=NetboxApp.IPAM, required=["name", "status", "vid"], filer=["vid"]
    ),
    "prefixes": Meta(
        app=NetboxApp.IPAM, required=["prefix", "status"], filer=["prefix"]
    ),
    "cables": Meta(
        app=NetboxApp.DCIM,
        required=["a_terminations", "b_terminations"],
        filer=["termination_a_id", "termination_b_id"],
    ),
}


def load_data(file_path):
    try:
        with open(file_path, "r") as file:
            return yaml.safe_load(file)

    except FileNotFoundError as e:
        logger.error(f"Failed to find {file_path}: {e}")
        sys.exit(1)


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

    except (pynetbox.RequestError, requests.exceptions.RequestException) as e:
        logger.error(f"Failed to get {nb_model.capitalize()}: {e}")
        sys.exit(1)


def mangle_secret(nb: pynetbox.api, params: dict):

    if "device" in params["data"]:
        device = params["data"].pop("device")
        params["data"].update(
            {
                "device": get_model_id(
                    nb,
                    "devices",
                    {"name": device},
                ),
            }
        )
        return

    logger.error(f"Unsupported secret values")
    sys.exit(1)


def mangle_ip_addresses(nb: pynetbox.api, params: dict):

    if "device" in params and "interface" in params:
        params.update(
            {
                "assigned_object_type": "dcim.interface",
                "assigned_object_id": get_model_id(
                    nb,
                    "interfaces",
                    {"device": params["device"], "name": params["interface"]},
                ),
            }
        )
        return

    logger.error(f"Unsupported ip-address values")
    sys.exit(1)


def mangle_interfaces(nb: pynetbox.api, params: dict):

    if "tagged_vlans" in params:
        tagged_vlans = params["tagged_vlans"]
        ids = []
        for tagged_vlan in tagged_vlans:
            ids.append(get_model_id(nb, "vlans", tagged_vlan))
        params.update({"tagged_vlans": ids})

    if "lag" in params:
        lag_id = get_model_id(
            nb,
            "interfaces",
            {"device": params["device"]["name"], "name": params["lag"]["name"]},
        )
        params.update({"lag": lag_id})


def mangle_cables(nb: pynetbox.api, params: dict):
    id_a = get_model_id(
        nb,
        "interfaces",
        {
            "device": params["a_terminations"]["device"],
            "name": params["a_terminations"]["interface"],
        },
    )
    id_b = get_model_id(
        nb,
        "interfaces",
        {
            "device": params["b_terminations"]["device"],
            "name": params["b_terminations"]["interface"],
        },
    )
    params.update(
        {
            "a_terminations": [{"object_type": "dcim.interface", "object_id": id_a}],
            "b_terminations": [{"object_type": "dcim.interface", "object_id": id_b}],
            # Note: filter params
            "termination_a_id": id_a,
            "termination_b_id": id_b,
        }
    )


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

    if nb_model == "cables":
        mangle_cables(nb, params)

    if nb_model == "ip-addresses" and "device" in params:
        mangle_ip_addresses(nb, params)

    if nb_model == "interfaces" and ("tagged_vlans" in params or "lag" in params):
        mangle_interfaces(nb, params)

    nb_filter = {}
    for key in nb_meta.filer:
        try:
            nb_filter_value = params[key]
        except KeyError:
            logger.error(f"{nb_model.capitalize()} missing filer parameter")
            sys.exit(1)

        # FIXME: improve this naive implementation
        if isinstance(nb_filter_value, Mapping) and nb_model != "cables":
            nested_key = "slug"
            if "name" in nb_filter_value:
                nested_key = "name"
            nb_filter.update({key: nb_filter_value[nested_key]})
        else:
            nb_filter.update({key: nb_filter_value})

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

    except (pynetbox.RequestError, requests.exceptions.RequestException) as e:
        logger.error(f"{nb_model.capitalize()} creation or update failed: {e}")
        sys.exit(1)


def sync_config_templates(nb: pynetbox.api, params: dict):
    try:
        config_template = nb.extras.config_templates.get(name=params["name"])
        # Note: It seems that pynetbox does not support the bellow call
        response = requests.post(
            f"{nb.base_url}/extras/config-templates/{config_template.id}/sync/",
            headers={
                "Authorization": f"Token {nb.token}",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        # Note: It seems that netbox does not report successful sync on config templates
        logger.info(f"Config template {config_template.name}: sync requested")

    except (pynetbox.RequestError, requests.exceptions.RequestException) as err:
        logger.error(f"Failed to sync config template {params['name']}: {err}")


def sync_data_source(nb: pynetbox.api, params: dict, wait_for_sync: int = 60):
    try:
        data_source = nb.core.data_sources.get(name=params["name"])
        # Note: It seems that pynetbox does not support the bellow call
        response = requests.post(
            f"{nb.base_url}/core/data-sources/{data_source.id}/sync/",
            headers={
                "Authorization": f"Token {nb.token}",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        logger.info(f"Data source {data_source.name}: sync requested")

        # Wait for sync to complete, checking `wait_for_sync` times at 1-second intervals
        for _ in range(wait_for_sync):
            time.sleep(1)
            data_source = nb.core.data_sources.get(id=data_source.id)

            if data_source.status.value == "completed":
                logger.info(f"Data source {data_source.name}: synced successfully")
                break

            logger.info(f"Data source {data_source.name}: waiting for sync")

        else:
            logger.error(
                f"Data source {data_source.name} sync did not complete within the timeout period"
            )
    except (pynetbox.RequestError, requests.exceptions.RequestException) as err:
        logger.error(f"Failed to sync data source {params['name']}: {err}")


def execute_script(nb: pynetbox.api, params: dict, wait_for_execute: int = 60):
    mangle_secret(nb, params)
    # Note: It seems that pynetbox does not support the bellow calls
    try:
        response = requests.get(
            f"{nb.base_url}/extras/scripts/",
            headers={
                "Authorization": f"Token {nb.token}",
                "Content-Type": "application/json",
            },
            params={"name": params["name"]},
        )
        response.raise_for_status()
        script_id = response.json()["results"][0]["id"]

        response = requests.post(
            f"{nb.base_url}/extras/scripts/{script_id}/",
            headers={
                "Authorization": f"Token {nb.token}",
                "Content-Type": "application/json",
            },
            json={"data": params.get("data"), "commit": True},
        )
        response.raise_for_status()

        logger.info(f"Script {params['name']}: execute requested")

        # Wait for sync to complete, checking `wait_for_execute` times at 1-second intervals
        for _ in range(wait_for_execute):
            time.sleep(1)
            status_response = requests.get(
                f"{nb.base_url}/extras/scripts/{script_id}/",
                headers={
                    "Authorization": f"Token {nb.token}",
                    "Content-Type": "application/json",
                },
            )
            status_response.raise_for_status()
            status_data = status_response.json()

            if (
                status_data.get("result", {}).get("status", {}).get("value")
                == "completed"
            ):
                logger.info(f"Script {params['name']}: executed successfully")
                break
            logger.info(f"Script {params['name']}: waiting for execute")

        else:
            logger.error(
                f"Script {params['name']} did not execute within the timeout period"
            )
    except requests.exceptions.RequestException as err:
        logger.error(f"Failed to execute script {params['name']}: {err}")


def environ_or_required(key):
    return (
        {"default": os.environ.get(key)} if os.environ.get(key) else {"required": True}
    )


def get_yaml_paths(directory):
    patterns = [os.path.join(directory, "*.yml"), os.path.join(directory, "*.yaml")]
    file_paths = []

    for pattern in patterns:
        file_paths.extend(glob.glob(pattern))

    file_paths.sort()

    return file_paths


parser = argparse.ArgumentParser(description="Bootstrap NetBox.")
parser.add_argument(
    "--api-url", "-u", **environ_or_required("NETBOX_URL"), help="NetBox instance URL"
)
parser.add_argument(
    "--api-token", "-t", **environ_or_required("NETBOX_TOKEN"), help="NetBox API token"
)
parser.add_argument(
    "--data-dir",
    "-d",
    help="Path to the netbox data directory. All YAML files will be processed in alphanumerical order.",
)
parser.add_argument(
    "--data-file",
    "-f",
    action="append",
    help="Path to the netbox data file. It could be used multiple times.",
)
parser.add_argument(
    "--sync-datasources",
    "-s",
    action="store_true",
    help="Sync NetBox data sources after its creation or update.",
)
parser.add_argument(
    "--sync-config-templates",
    "-sc",
    action="store_true",
    help="Sync NetBox config templates after its creation or update.",
)
parser.add_argument(
    "--execute-scripts",
    "-e",
    action="store_true",
    help="Execute Netbox custom scripts",
)


if __name__ == "__main__":
    args = parser.parse_args()
    nb = pynetbox.api(args.api_url, token=args.api_token)

    file_paths = []
    if args.data_dir:
        file_paths.extend(get_yaml_paths(args.data_dir))

    if args.data_file:
        file_paths.extend([file for file in args.data_file])

    for file_path in file_paths:
        data = load_data(file_path)
        for nb_model, items in data.items():

            for params in items:
                # Note: The `scripts` is custom resource field introduced to manage the scripts execution
                # Scripts are executed only when the optional argument `--execute-scripts` is applied.
                if nb_model == "scripts":
                    if args.execute_scripts:
                        execute_script(nb, params)
                    continue

                create_or_update(nb, nb_model, params)

                if nb_model == "data-sources" and args.sync_datasources:
                    sync_data_source(nb, params)

                if nb_model == "config-templates" and args.sync_config_templates:
                    sync_config_templates(nb, params)
