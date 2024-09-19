#!/bin/bash

# TODOs:
# - some validations are ignored, see https://github.com/osism/python-osism/pull/1054
# - There is no "all" validations target

echo "Logging validations to /tmp/validate.log"
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
) 2>&1 |tee /tmp/validate.log
