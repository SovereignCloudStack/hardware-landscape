#!/bin/bash

FAILED=""

if [ $(openstack compute service list --os-cloud admin -f json|jq '.[] | select(.Status != "enabled" or .State != "up")'|wc -l) -gt 0 ];then
	FAILED="NODES-DOWN"
	openstack compute service list --os-cloud admin
fi	

if [ -z "FAILED" ];then
	echo "FAILED: $FAILED"
	exit 1
fi
