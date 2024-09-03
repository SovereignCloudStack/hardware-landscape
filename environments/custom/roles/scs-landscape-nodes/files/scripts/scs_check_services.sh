#!/bin/bash

failed="false"
systemctl list-units --state=failed|grep failed
if [ "$?" = "0" ];then
   echo "ERROR: failed units"
   failed="true"
fi

exited="$(docker ps -a --filter "status=exited")"
echo "$exited"

if [ "$(echo "$exited"|wc -l)" -gt 1 ];then
   failed="true"
fi

if [ "$failed" == "true" ];then
   echo "ERROR: exited containers"
   exit 1
else
   exit 0
fi
