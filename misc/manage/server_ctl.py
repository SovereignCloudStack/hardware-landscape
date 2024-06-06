#!/usr/bin/env python3

import argparse
import sys
from pprint import pprint

from lib.server_operating_system import install_server, control_servers, open_servers, check_power_servers, \
    PowerActionTypes, create_configs
from lib.helpers import template_ansible_config
from lib.server_hardware import template_bmc_config, backup_config, restore_config, CfgTypes
from lib.global_helpers import setup_logging
from lib.server_model import get_unique_servers

parser = argparse.ArgumentParser(
    prog='Configure Servers')

parser.add_argument('node', metavar='host', help="One or more hostnames, use 'all' as a"
                                                 " shortcut for all servers", type=str, nargs='+')

exclusive_group = parser.add_mutually_exclusive_group(required=True)

exclusive_group.add_argument('--open', '-o', action="store_true",
                             help="Open hosts in your preferred browser and output the login credentials")

exclusive_group.add_argument('--bmc_template', action="store_true",
                             help='Modify existing bmc configuration')

exclusive_group.add_argument('--install_os', '-i', action="store_true",
                             help='Install a server os')

exclusive_group.add_argument('--power_action', choices=[e.name for e in PowerActionTypes],
                             help='Perform a power action')

exclusive_group.add_argument('--power_check', action="store_true",
                             help='Check power status')

exclusive_group.add_argument('--show', '-s', action="store_true",
                             help="Show hosts")

exclusive_group.add_argument('--ansible', '-a', action="store_true",
                             help="Create ansible inventory files")

exclusive_group.add_argument('--backup_cfg', choices=[e.name for e in CfgTypes],
                             help='backup system configuration (possible values: both, bmc, bios)')

exclusive_group.add_argument('--restore_cfg', choices=[e.name for e in CfgTypes],
                             help='restore system configuration (possible values: both, bmc, bios)')

exclusive_group.add_argument('--configs', '-c', help="create config snippets for environment", action='store_true')

parser.add_argument('--watch', '-w', action="store_true",
                    help="Open hosts in your preferred browser and output the login credentials")

parser.add_argument('--media_url', metavar='url', type=str,
                    default="auto",
                    help='The URL for for the iso image')

parser.add_argument('--log_level', metavar='loglevel', type=str,
                    default="INFO", help='The loglevel')

parser.add_argument('--filter', '-f', metavar='loglevel', type=str,
                    default=None, help='A filter expression <key>=<regex for values>')

parser.add_argument('--verbose', '-v', action='store_true')

args = parser.parse_args()

setup_logging(args.log_level)

if args.bmc_template:
    template_bmc_config(get_unique_servers(args.node, False, args.filter))

if args.ansible:
    template_ansible_config(get_unique_servers(args.node, False, args.filter))

if args.install_os:
    install_server(get_unique_servers(args.node, False, args.filter), args.media_url, args.watch)

if args.power_action:
    control_servers(get_unique_servers(args.node, False, args.filter), args.power_action)

if args.power_check:
    check_power_servers(get_unique_servers(args.node, False, args.filter))

if args.backup_cfg:
    backup_config(get_unique_servers(args.node, False, args.filter), args.backup_cfg)

if args.restore_cfg:
    restore_config(get_unique_servers(args.node, False, args.filter), args.restore_cfg)

if args.show:
    print()
    print("The following hosts are configured:", file=sys.stderr)
    hosts = get_unique_servers(args.node, args.verbose, args.filter)
    for host in hosts:
        pprint(host, indent=2)

if args.open:
    open_servers(get_unique_servers(args.node, False, args.filter))
    sys.exit(0)

if args.configs:
    create_configs(get_unique_servers(args.node, False, args.filter))



sys.exit(0)
