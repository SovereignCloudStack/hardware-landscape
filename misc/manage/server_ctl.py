#!/usr/bin/env python3

import argparse
import sys

from lib.server_operating_system import install_server, control_servers, open_servers, check_power_servers, \
    template_ansible_config
from lib.server_hardware import template_bmc_config, backup_config, restore_config, CfgTypes
from lib.helpers import get_unique_hosts, get_unique_hosts_full, setup_logging, get_basedir

parser = argparse.ArgumentParser(
    prog='Configure Servers')

parser.add_argument('node', metavar='host', default=["all"], type=str, nargs='*')

exclusive_group = parser.add_mutually_exclusive_group(required=True)

exclusive_group.add_argument('--bmc_template', action="store_true",
                             help='Modify existing bmc configuration')

exclusive_group.add_argument('--install_os', '-i', action="store_true",
                             help='Install a server os')

exclusive_group.add_argument('--power_off', action="store_true",
                             help='Stop system')
exclusive_group.add_argument('--power_on', action="store_true",
                             help='Start system')
exclusive_group.add_argument('--power_check', action="store_true",
                             help='Check power status')

exclusive_group.add_argument('--show', '-s', action="store_true",
                             help="Show hosts")

exclusive_group.add_argument('--ansible', '-a', action="store_true",
                             help="Create ansible inventory files")

exclusive_group.add_argument('--backup_cfg', type=CfgTypes,
                             help='backup system configuration (possible values: both, bmc, bios)')

exclusive_group.add_argument('--restore_cfg', type=CfgTypes,
                             help='restore system configuration (possible values: both, bmc, bios)')


exclusive_group.add_argument('--open','-o', action="store_true",
                             help="Open hosts in your preferred browser and output the login credentials")

parser.add_argument('--media_url', metavar='url', type=str,
                    default="http://10.10.23.1/ubuntu-autoinstall-osism-4.iso",
                    help='The URL for for the iso image')

parser.add_argument('--log_level', metavar='loglevel', type=str,
                    default="INFO", help='The loglevel')

parser.add_argument('--verbose', '-v', action='store_true')

args = parser.parse_args()

setup_logging(args.log_level)

if args.show:
    print()
    print("The following hosts are configured:")
    if args.verbose:
        hosts = get_unique_hosts_full(args.node)
    else:
        hosts = get_unique_hosts(args.node)

    for host in hosts:
        print(host)


if args.open:
    open_servers(get_unique_hosts(args.node))
    sys.exit(0)

if args.bmc_template:
    template_bmc_config(get_unique_hosts(args.node))

if args.ansible:
    template_ansible_config(get_unique_hosts(args.node))

if args.install_os:
    install_server(get_unique_hosts(args.install_os), args.media_url)

if args.power_on:
    control_servers(get_unique_hosts(args.node), "ForceOn")

if args.power_off:
    control_servers(get_unique_hosts(args.node), "ForceOff")

if args.power_check:
    check_power_servers(get_unique_hosts(args.node))

if args.backup_cfg:
    backup_config(get_unique_hosts(args.node), args.backup_cfg)

if args.restore_cfg:
    restore_config(get_unique_hosts(args.node), args.restore_cfg)

sys.exit(0)