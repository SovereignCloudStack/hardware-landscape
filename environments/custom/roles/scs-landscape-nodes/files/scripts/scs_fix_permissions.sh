#!/bin/bash
set -x

fix_perm(){
   sudo find $1 -type d -exec chmod 770 {} +
   sudo find $1 -type f -exec chmod 660 {} +
   sudo find $1 -type f \( -name "*.sh" -or -name "*_ctl" -or -path "*/venv/bin/*" -or -path "*/.venv/bin/*" \) -exec chmod 770 {} +
   sudo find $1 -exec chown dragon:dragon {} +
}

fix_perm /usr/local/scripts
fix_perm /opt/configuration
git config --global --add safe.directory /opt/configuration

