#!/bin/bash

cd /opt/configuration/environments/openstack || exit 1

set -x 
set -e
openstack service list --long
openstack endpoint list
openstack volume service list
openstack compute service list
openstack hypervisor list
openstack network agent list
openstack network service provider list

