#!/bin/bash


failed=""
grep -P "st01-(stor|mgmt|comp|ctl)-r\d+-u\d+" /etc/hosts|awk '{print $(NF)}'|sort|while read node
do
   ping -q -c 2 $node
   if [ "$?" != "0" ];then
      failed="$node $failed"
   fi
done

if [ -z "$failed" ];then
   echo "OK"
   exit 0
else
   echo "FAILED: $failed"
   exit 1
fi

