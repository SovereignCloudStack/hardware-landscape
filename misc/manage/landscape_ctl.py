#!/usr/bin/env python3

import argparse
import sys

from lib.global_helpers import setup_logging
from openstack import connection
from openstack.config import loader

from lib.landscape import SCSLandscapeTestDomain, SCSLandscapeTestProject

parser = argparse.ArgumentParser(
    prog='Manage Landscape')

parser.add_argument('--log_level', metavar='loglevel', type=str,
                    default="INFO", help='The loglevel')

parser.add_argument('--os_cloud', type=str,
                    default="vp18", help='The openstack config')

parser.add_argument('--verbose', '-v', action='store_true')

exclusive_group = parser.add_mutually_exclusive_group(required=True)

exclusive_group.add_argument('--create_domains', '-c', type=str, nargs="+", default=None,
                             help='A list of domains to be created')

exclusive_group.add_argument('--delete_domains', '-d', type=str, nargs="+", default=None,
                             help='A list of domains to be deleted')

parser.add_argument('--create_projects', '-p', type=str, nargs="+", default=["test1"],
                             help='A list of projects to be created in the created domains')

parser.add_argument('--create_machines', '-m', type=str, nargs="+", default=["test1"],
                             help='A list of vms to be created in the created domains')
args = parser.parse_args()

setup_logging(args.log_level)

config = loader.OpenStackConfig()
cloud_config = config.get_one(args.os_cloud)
conn = connection.Connection(config=cloud_config)


if args.create_domains:
    domains: list[SCSLandscapeTestDomain] = []
    for domain_name in args.create_domains:
        domain = SCSLandscapeTestDomain(conn, domain_name)
        domain.create_and_get_domain()
        domain.create_and_get_projects(args.create_projects)

        for project in domain.scs_projects:
            project.get_and_create_machines(args.create_machines)

if args.delete_domains:
    for domain_name in args.delete_domains:
        os = SCSLandscapeTestDomain(conn, domain_name)
        os.delete_domain()

sys.exit(0)
