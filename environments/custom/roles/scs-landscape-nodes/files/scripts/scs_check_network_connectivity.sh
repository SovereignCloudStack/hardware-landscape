#!/bin/bash


failed=""

sudo vtysh -c "show ip bgp summary"
while read interface
do
   failed="NEIGHBOR:$node $failed"
done < <(sudo vtysh -c "show ip bgp summary"|awk '/^enp/{if ($10 !~/[0-9][0-9]*/){print $1;exit 1}}')


while read node
do
   ping -M do -c ${1:-2} -s $((9100 - 28)) $node
   if [ "$?" != "0" ];then
      failed="PING:$node $failed"
   fi
done < <(grep -P "st01-(stor|mgmt|comp|ctl)-r\d+-u\d+" /etc/hosts|awk '{print $(NF)}'|sort)


if [ -z "$failed" ];then
   echo "OK"
   exit 0
else
   echo "FAILED: $failed"
   exit 1
fi

