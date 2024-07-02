#!/bin/bash

add_rule(){
   local POS_WANTED="$1"
   local RULE="$2"
   local RULE_EXISTS="false"
   local OUTDATED_RULES_HANDLES=""
   local RULE_MARKER="SCS-MASQ"

   while read RULE_HANDL POS;
   do
      if ( [ "$POS" = "${POS_WANTED}" ] && [ "$1" != "force" ] );then
         RULE_EXISTS="true"
      else
         OUTDATED_RULES_HANDLES="$RULE_HANDL $OUTDATED_RULES_HANDLES"
      fi
   done < <(nft -a list chain nat POSTROUTING|awk -v "marker=$RULE_MARKER" '
      BEGIN{ pos=-1; }
      $0 ~ marker {printf("%s %s\n",$(NF),pos); }
      /# handle [0-9][0-9]*/{ pos++; }'
   )

   if ( [ "$FORCE" = "force" ] || [ "$RULE_EXISTS" != "true" ] );then
      echo "adding rule to position ${POS_WANTED}"|logger -s -t scs_add_netfilter_rules
      nft insert rule "ip nat POSTROUTING position ${POS_WANTED} limit rate 30/minute log prefix $RULE_MARKER $RULE"
   else
      echo "rule already on position ${POS_WANTED}"|logger -s -t scs_add_netfilter_rules
   fi


   for RULE_HANDL in $OUTDATED_RULES_HANDLES;
   do
      echo "removing handle $RULE_HANDL"|logger -s -t scs_add_netfilter_rules
      nft delete rule nat POSTROUTING handle $RULE_HANDL
   done
}

FORCE="${1:-add}"
add_rule 0 'ip saddr { 172.31.100.0/23, 10.10.1.0/24 } ip daddr 10.10.21.0/24 snat to 10.10.21.10'
add_rule 0 'ip saddr { 172.31.100.0/23, 10.10.1.0/24 } ip daddr 10.10.23.0/24 snat to 10.10.23.254'
