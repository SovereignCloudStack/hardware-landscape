#!/bin/bash


OLD_RULES="$(nft -a list chain nat POSTROUTING|awk -v "marker=SCS-MASQ" '$0 ~ marker {printf("%s ",$(NF)); }')"

LOG=''
if [ "$1" = "log" ];then
   LOG='log prefix "SCS-MASQ "'
fi

mkdir -p /var/backups/nft
nft list ruleset > /var/backups/nft/nft-`date --date="today" "+%Y-%m-%d_%H-%M-%S"`.nft
find /var/backups/nft -mtime +30 -type f -delete

set -x 
nft "insert rule ip nat POSTROUTING position 0 $LOG ip saddr 172.31.100.0/23 ip daddr 10.10.21.0/24 snat to 10.10.21.10 comment SCS-MASQ"
nft "insert rule ip nat POSTROUTING position 0 $LOG ip saddr 172.31.100.0/23 ip daddr 10.10.22.0/24 snat to 10.10.21.1 comment SCS-MASQ"
nft "insert rule ip nat POSTROUTING position 0 $LOG ip saddr 172.31.100.0/23 ip daddr 10.10.23.0/24 snat to 10.10.23.254 comment SCS-MASQ"
nft "insert rule ip nat POSTROUTING position 0 $LOG ip saddr 10.10.1.0/24 ip daddr 10.10.21.0/24 snat to 10.10.21.10 comment SCS-MASQ"
nft "insert rule ip nat POSTROUTING position 0 $LOG ip saddr 10.10.1.0/24 ip daddr 10.10.22.0/24 snat to 10.10.21.1 comment SCS-MASQ"
nft "insert rule ip nat POSTROUTING position 0 $LOG ip saddr 10.10.1.0/24 ip daddr 10.10.23.0/24 snat to 10.10.23.254 comment SCS-MASQ"
set +x
for rule in $OLD_RULES; do
   echo "remove rule with handle $rule"
   nft delete rule nat POSTROUTING handle $rule
done

