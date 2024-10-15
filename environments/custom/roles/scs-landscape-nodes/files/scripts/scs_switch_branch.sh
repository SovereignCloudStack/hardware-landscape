#!/bin/bash

BRANCH="$1"
if [ -z "$BRANCH" ];then
  echo "$0 <branch>"
  exit 1
fi
export PATH="$PATH:/usr/local/scripts/"

logger -t scs -s "Switching to branch $BRANCH now"
set -x
set -e
scs_fix_permissions.sh
cd /opt/configuration
git pull
git checkout $BRANCH
sed -i "~s,^configuration_git_version:.*\$,configuration_git_version: ${BRANCH}," environments/manager/configuration.yml
git diff || true
read -p CONTINUE
git diff 
git commit -s environments/manager/configuration.yml
sudo -u dragon osism sync configuration
sudo -u dragon osism sync inventory
sudo -u dragon osism apply facts
logger -t scs -s "Switching to branch $BRANCH completed"
