#!/usr/bin/env bash

# DO NOT EDIT THIS FILE BY HAND -- YOUR CHANGES WILL BE OVERWRITTEN

ANSIBLE_COLLECTION_COMMONS_VERSION=${ANSIBLE_COLLECTION_COMMONS_VERSION:-main}
ANSIBLE_COLLECTION_SERVICES_VERSION=${ANSIBLE_COLLECTION_SERVICES_VERSION:-main}
ANSIBLE_PLAYBOOKS_MANAGER_VERSION=${ANSIBLE_PLAYBOOKS_MANAGER_VERSION:-main}

ANSIBLE_COLLECTION_COMMONS_SOURCE=${ANSIBLE_COLLECTION_COMMONS_SOURCE:-git+https://github.com/osism/ansible-collection-commons}
ANSIBLE_COLLECTION_SERVICES_SOURCE=${ANSIBLE_COLLECTION_SERVICES_SOURCE:-git+https://github.com/osism/ansible-collection-services}
ANSIBLE_PLAYBOOKS_MANAGER_SOURCE=${ANSIBLE_PLAYBOOKS_MANAGER_SOURCE:-git+https://github.com/osism/ansible-playbooks-manager}

INSTALL_ANSIBLE=${INSTALL_ANSIBLE:-true}
INSTALL_ANSIBLE_ROLES=${INSTALL_ANSIBLE_ROLES:-true}
VENV_PATH=${VENV_PATH:-venv}
VENV_PYTHON_BIN=${VENV_PYTHON_BIN:-python3}

RUNDIR="$(dirname $(readlink -f $0))"
cd $RUNDIR || exit 1


if [[ $# -lt 1 ]]; then
    echo "usage: $0 PLAYBOOK [ANSIBLEARGS...]"
    exit 1
fi

playbook=$1
shift

if [[ $INSTALL_ANSIBLE == "true" ]]; then
    if [[ ! -e $VENV_PATH ]]; then

        command -v virtualenv >/dev/null 2>&1 || { echo >&2 "virtualenv not installed"; exit 1; }

        virtualenv -p "$VENV_PYTHON_BIN" "$VENV_PATH"
        # shellcheck source=/dev/null
        source "$VENV_PATH/bin/activate"
        pip3 install -r requirements.txt

    else

        # shellcheck source=/dev/null
        source "$VENV_PATH/bin/activate"

    fi
fi

command -v ansible-playbook >/dev/null 2>&1 || { echo >&2 "ansible-playbook not installed"; exit 1; }
command -v ansible-galaxy >/dev/null 2>&1 || { echo >&2 "ansible-galaxy not installed"; exit 1; }

configured_branch="$(grep -E "^configuration_git_version:"  $RUNDIR/configuration.yml|sed '~s,^..*:[ ]*,,')"
current_branch="$(git rev-parse --abbrev-ref HEAD)"

if [ "$configured_branch" != "$current_branch" ];then
   echo "ERROR:"
   echo "Configured branch '$configured_branch' (see configuration.yml, configuration_git_version)"
   echo "and current branch '$current_branch' are not the same! Exiting!"
   exit 1
fi

ANSIBLE_USER=${ANSIBLE_USER:-dragon}
CLEANUP=${CLEANUP:-false}

cleanup () {
    if [[ $CLEANUP == "true" ]]; then
        rm id_rsa.operator
        rm -rf "$VENV_PATH"
    fi
}
trap cleanup ERR EXIT

if [[ $INSTALL_ANSIBLE_ROLES == "true" ]]; then
    ansible-galaxy collection install -f "${ANSIBLE_COLLECTION_COMMONS_SOURCE},${ANSIBLE_COLLECTION_COMMONS_VERSION}"
    ansible-galaxy collection install -f "${ANSIBLE_COLLECTION_SERVICES_SOURCE},${ANSIBLE_COLLECTION_SERVICES_VERSION}"
    ansible-galaxy collection install -f "${ANSIBLE_PLAYBOOKS_MANAGER_SOURCE},${ANSIBLE_PLAYBOOKS_MANAGER_VERSION}"
fi

if [[ ! -e id_rsa.operator ]]; then
    ansible-playbook \
        -i localhost, \
        -e @../secrets.yml \
        -e "keypair_dest=$(pwd)/id_rsa.operator" \
        osism.manager.keypair "$@" || exit $?
fi

if [[ $playbook == "k8s" || $playbook == "netbox" || $playbook == "traefik" ]]; then
    ansible-playbook \
        --private-key id_rsa.operator \
        -i hosts \
        -e @../images.yml \
        -e @../configuration.yml \
        -e @../secrets.yml \
        -e @../infrastructure/images.yml \
        -e @../infrastructure/configuration.yml \
        -e @../infrastructure/secrets.yml \
        -e @images.yml \
        -e @configuration.yml \
        -e @secrets.yml \
        -u "$ANSIBLE_USER" \
        osism.manager."$playbook" "$@" || exit $?
elif [[ $playbook == "operator" ]]; then
    if [[ $ANSIBLE_ASK_PASS == "True" ]]; then
        ansible-playbook \
            -i hosts \
            -e @../images.yml \
            -e @../configuration.yml \
            -e @../secrets.yml \
            -e @images.yml \
            -e @configuration.yml \
            -e @secrets.yml \
            -u "$ANSIBLE_USER" \
            osism.manager."$playbook" "$@" || exit $?
    else
        ansible-playbook \
            --private-key id_rsa.operator \
            -i hosts \
            -e @../images.yml \
            -e @../configuration.yml \
            -e @../secrets.yml \
            -e @images.yml \
            -e @configuration.yml \
            -e @secrets.yml \
            -u "$ANSIBLE_USER" \
            osism.manager."$playbook" "$@" || exit $?
    fi
else
    ansible-playbook \
        --private-key id_rsa.operator \
        -i hosts \
        -e @../images.yml \
        -e @../configuration.yml \
        -e @../secrets.yml \
        -e @images.yml \
        -e @configuration.yml \
        -e @secrets.yml \
        -u "$ANSIBLE_USER" \
        osism.manager."$playbook" "$@" || exit $?
fi