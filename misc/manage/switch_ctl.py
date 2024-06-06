#!/usr/bin/env python3

import argparse
import sys
from pprint import pprint

from lib.global_helpers import setup_logging
from lib.switch_model import get_unique_switches
from lib.switch_operating_system import CfgTypes
from lib.helpers import template_ansible_config

parser = argparse.ArgumentParser(
    prog='Configure Switches')

parser.add_argument('node', metavar='host', help="One or more hostnames, use 'all' as a"
                                                 " shortcut for all switches", type=str, nargs='+')

exclusive_group = parser.add_mutually_exclusive_group(required=True)

exclusive_group.add_argument('--show', '-s', action="store_true",
                             help="Show hosts")

exclusive_group.add_argument('--ansible', '-a', action="store_true",
                             help="Create ansible inventory files")

exclusive_group.add_argument('--backup_cfg', type=CfgTypes,
                             help='backup system configuration (possible values: both, bmc, bios)')

exclusive_group.add_argument('--restore_cfg', type=CfgTypes,
                             help='restore system configuration (possible values: both, bmc, bios)')

parser.add_argument('--log_level', metavar='loglevel', type=str,
                    default="INFO", help='The loglevel')

parser.add_argument('--filter', '-f', metavar='loglevel', type=str,
                    default=None, help='A filter expression <key>=<regex for values>')

parser.add_argument('--verbose', '-v', action='store_true')

args = parser.parse_args()

setup_logging(args.log_level)

if args.ansible:
    template_ansible_config(get_unique_switches(args.node, False, args.filter), "switches")
#
# if args.backup_cfg:
#     backup_config(get_unique_hosts(args.node), args.backup_cfg)
#
# if args.restore_cfg:
#     restore_config(get_unique_hosts(args.node), args.restore_cfg)

if args.show:
    print()
    print("The following switches are configured:", file=sys.stderr)
    hosts = get_unique_switches(args.node, args.verbose, args.filter)
    for host in hosts:
        pprint(host, indent=2)

sys.exit(0)
