#!/bin/bash

# TODOs:
# - some validations are ignored, see https://github.com/osism/python-osism/pull/1054
# - There is no "all" validations target

LOGFILE="/var/log/validations-$(date --date="today" "+%Y-%m-%d_%H-%M-%S")"

echo "Logging validations to $LOGFILE"
(
FAILED=""
while read val; do 
	echo "** VALIDATION: $val"; 
	osism validate $val
	if [ "$?" != "0" ];then
		FAILED="$FAILED $val"
		echo "VALIDATION FAILED"
	fi
done < <(osism validate 2>&1|grep barbican|tr '{,}' '\n\n\n'|grep -v -P "(mariadb-backup|mariadb-recovery|senlin-config)"|grep "[a-z]")

echo "FAILED VALIDATIONS: ${FAILED:-none}"
) 2>&1 |sudo tee $LOGFILE
