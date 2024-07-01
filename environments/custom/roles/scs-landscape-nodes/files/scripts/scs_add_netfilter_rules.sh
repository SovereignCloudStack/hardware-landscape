#!/bin/bash

RULE_EXISTS="false"
OUTDATED_RULES_HANDLES=""
RULE_MARKER="SCS-MASQUERADING"

while read RULE_HANDL POS;
do
   if ( [ "$POS" = "0" ] && [ "$1" != "force" ] );then
      RULE_EXISTS="true"
   else
      OUTDATED_RULES_HANDLES="$RULE_HANDL $OUTDATED_RULES_HANDLES"
   fi
done < <(nft -a list chain nat POSTROUTING|awk -v "marker=$RULE_MARKER" '
   BEGIN{ pos=-1; }
   $0 ~ marker {printf("%s %s\n",$(NF),pos); }
   /# handle [0-9][0-9]*/{ pos++; }'
)

if [ "$RULE_EXISTS" != "true" ];then
   echo "adding rule to position 0"|logger -s -t scs_add_netfilter_rules
   nft insert rule ip nat POSTROUTING position 0 log prefix $RULE_MARKER ip saddr "{ 172.31.100.0/23, 10.10.1.0/24 }" ip daddr 10.10.21.0/24 snat to 10.10.21.10
else
   echo "rule already on position 0"|logger -s -t scs_add_netfilter_rules
fi


for RULE_HANDL in $OUTDATED_RULES_HANDLES;
do
   echo "removing handle $RULE_HANDL"|logger -s -t scs_add_netfilter_rules
   nft delete rule nat POSTROUTING handle $RULE_HANDL
done
