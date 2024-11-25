#!/usr/bin/env python3

import argparse
import json
import logging
import sys

from lib.global_helpers import setup_logging, get_ansible_secrets
from lib.helpers import filter_dict_keys, print_all_dict_values

LOGGER = logging.getLogger()

parser = argparse.ArgumentParser(
    prog='Basic Landscape Management')

parser.add_argument('--log_level', metavar='loglevel', type=str,
                    default="INFO", help='The loglevel')

parser.add_argument('--only_values', '-o', action="store_true",
                             help="Show only the values")

parser.add_argument('--show_secrets', '-s', type=str, nargs="+", default="all",
                             help='Show all or a number of secrets matched by regexes')

args = parser.parse_args()

setup_logging(args.log_level)

if args.show_secrets:
    if "all" in args.show_secrets:
        args.show_secrets = [".*"]
    secret_data = filter_dict_keys(get_ansible_secrets(), args.show_secrets)
    if args.only_values:
        if print_all_dict_values(secret_data) > 1:
            LOGGER.warning("More than one result discovered")
            sys.exit(1)
    else:
        print(json.dumps(secret_data, indent=2))
    sys.exit(0)

sys.exit(0)
