#!/bin/bash


OLD_RULES="$(nft -a list chain nat POSTROUTING|awk -v "marker=SCS-MASQ" '$0 ~ marker {printf("%s ",$(NF)); }')"

LOG=''
if [ "$1" = "log" ];then
   LOG='log prefix "SCS-MASQ "'
fi

mkdir -p /var/backups/nft
BACKUP_FILE="/var/backups/nft/nft-`date --date="today" "+%Y-%m-%d_%H-%M-%S"`.nft"

echo "create backup of old rules: $BACKUP_FILE"|logger -s -t scs_add_nftables_rules
nft list ruleset > $BACKUP_FILE
find /var/backups/nft -mtime +30 -type f -delete

ZONE1_IPV4="$(ip -json addr ls | jq -r '.[] | .addr_info[] | select(.local | startswith("10.10.21")) | .local')"
MGMT_IPV4="$(ip -json addr ls | jq -r '.[] | .addr_info[] | select(.local | startswith("10.10.23")) | .local')"
MGMTP2P_IPV4="$(ip -json addr ls | jq -r '.[] | .addr_info[] | select(.local | startswith("10.10.22")) | .local')"

echo "add standard rules"|logger -s -t scs_add_nftables_rules
set -x
nft "insert rule ip nat POSTROUTING position 0 $LOG ip saddr 172.31.100.0/23 ip daddr 10.10.21.0/24 snat to $ZONE1_IPV4 comment SCS-MASQ"
nft "insert rule ip nat POSTROUTING position 0 $LOG ip saddr 10.10.1.0/24 ip daddr 10.10.21.0/24 snat to $ZONE1_IPV4 comment SCS-MASQ"

nft "insert rule ip nat POSTROUTING position 0 $LOG ip saddr 172.31.100.0/23 ip daddr 10.10.23.0/24 snat to $MGMT_IPV4 comment SCS-MASQ"
nft "insert rule ip nat POSTROUTING position 0 $LOG ip saddr 10.10.1.0/24 ip daddr 10.10.23.0/24 snat to $MGMT_IPV4 comment SCS-MASQ"
set +x

if [ -n "$MGMTP2P_IPV4" ];then
	set -x
   echo "add MGMTP2P_IPV4 rules"|logger -s -t scs_add_nftables_rules
	nft "insert rule ip nat POSTROUTING position 0 $LOG ip saddr 10.10.1.0/24 ip daddr 10.10.22.0/24 snat to $MGMTP2P_IPV4 comment SCS-MASQ"
	nft "insert rule ip nat POSTROUTING position 0 $LOG ip saddr 172.31.100.0/23 ip daddr 10.10.22.0/24 snat $MGMTP2P_IPV4 comment SCS-MASQ"
	set +x
fi

for rule in $OLD_RULES; do
   echo "remove rule with handle $rule"|logger -s -t scs_add_nftables_rules
   nft delete rule nat POSTROUTING handle $rule
done

