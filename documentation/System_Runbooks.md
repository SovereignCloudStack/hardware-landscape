# Runbooks of the Hardware Landscape

# How to get access

## Manage SSH Access and Adminstrative Permissions

1. **User**: Clone repository and create PR
   ```
   git clone git@github.com:SovereignCloudStack/hardware-landscape.git
   cd hardware-landscape
   ```
2. **User**: Edit [environments/configuration.yml](../environments/configuration.yml)
  * Create branch
  * Make modifications for node access:
    * Add new users in `user_list` section
    * Actively remove users by adding them in the `user_delete`
  * Make modifications for switch access:
    * Change the operator_sonic_list to add or remove users
  * Create pull request to `main` branch
3. **Admin**: Rollout changes
   ```
   ssh scs-manager
   osism apply user
   osism apply operator
   osism apply scs_sonic_minimal
   ```
4. **User**: [Configure and use SSH Access](./System_Usage.md)
5. Inform user

## Manage VPN Access

1. **User**: [Create key](./System_Usage.md)
2. **Admin**: Rollout changes
   ```
   ssh scs-manager
   osism apply scs_infra
   ```
3. **Admin**: Inform user

## Have the Ansible Vault Secret on your system

Get the Ansible vault secret:

```
cd hardware-landscape
ssh scs-manager docker exec osism-ansible /ansible-vault.py
mkdir -p secrets
ssh scs-manager docker exec osism-ansible /ansible-vault.py > secrets/vaultpass
```

# Finding problems

## Checking the status of the system landscape

This ansible play executes basic diagnostic checks to simply problem detection:
```
ssh scs-manager
osism apply scs_check_landscape
```

# Shutdown the entire environment

This procedure describes the tasks to shutdown the scs hardware landscape completly.

* Local: Shutdown Compute Nodes
  ```
  NODES="st01-comp-r01-u15 st01-comp-r01-u17 st01-comp-r01-u19"
  for node in $NODES; do echo "--> $node"; ssh $node "sudo systemctl disable docker.service"; done
  for node in $NODES; do echo "--> $node"; ssh $node "sudo halt"; done
  ./server_ctl -o $NODES
  ./server_ctl --power_action ForceOff $NODES
  ./server_ctl --power_check $NODES
  ```
* Local: Shutdown Compute Nodes with Neutron Nodes
  ```
  NODES="st01-comp-r01-u09 st01-comp-r01-u11 st01-comp-r01-u13"
  for node in $NODES; do echo "--> $node"; ssh $node "sudo systemctl disable docker.service"; done
  for node in $NODES; do echo "--> $node"; ssh $node "sudo halt"; done
  ./server_ctl -o $NODES
  ./server_ctl --power_action ForceOff $NODES
  ./server_ctl --power_check $NODES
  ```
* Remote: Prepare Ceph for shutdown
  see https://osism.tech/docs/guides/operations-guide/ceph#shutdown-a-ceph-cluster
  ```
  ssh scs-manager
  ceph osd set noout
  ceph osd set nobackfill
  ceph osd set norecover
  ceph osd set norebalance
  ceph osd set nodown
  ceph osd set pause
  ```

* Shutdown Ceph OSDs
  ```
  NODES="$(./server_ctl -s all 2>/dev/null|grep -- "st01-stor")"
  for node in $NODES; do echo "--> $node"; ssh $node "sudo systemctl disable docker.service"; done
  for node in $NODES; do echo "--> $node"; ssh $node "sudo halt"; done
  ./server_ctl -o $NODES
  ./server_ctl --power_action ForceOff $NODES
  ./server_ctl --power_check $NODES
  ```
* Shutdown Ceph and Openstack Services
  ```
  NODES="$(./server_ctl -s all 2>/dev/null|grep -- "st01-ctl"|sort -r)"
  for node in $NODES; do
    echo "--> $node";
    echo "+sudo systemctl disable docker.service"
    ssh $node "sudo systemctl disable docker.service";
    echo "+sudo systemctl stop ceph\*"
    ssh $node "sudo systemctl stop ceph\*";
    echo "+sudo systemctl stop kolla\*"
    ssh $node "sudo systemctl stop kolla\*";
    ssh $node "docker ps"
    while [ $(ssh $node docker ps|wc -l) -gt 1 ]; do ssh $node docker ps; echo -e "\nwaiting"; sleep 5; done
  done
  ```

* Shutdown Controllers (Ceph and Openstack)
  ```
  NODES="$(./server_ctl -s all 2>/dev/null|grep -- "st01-ctl")"
  for node in $NODES; do echo "--> $node"; ssh $node "sudo halt"; done
  ./server_ctl -o $NODES
  ./server_ctl --power_action ForceOff $NODES
  ./server_ctl --power_check $NODES
  ```
* Shutdown Switches
  ```
  ./switch_ctl -s all 2>/dev/null|grep st01-sw| while read host; do echo "** $host";echo ssh ${host}-bmc "sudo halt"; done
  ```
* Shutdown Managers
  ```
  ssh st01-mgmt-r01-u31 sudo halt
  ./server_ctl --power_action ForceOff st01-mgmt-r01-u31
  ./server_ctl --power_check st01-mgmt-r01-u31

  sudo halt
  ```
# Startup the entire environment

This procedure describes the tasks ro startup a completly stopped scs hardware landscape.

* Startup both manager nodes with remote hands
  * check that they have a link on the "eno2" Interface (see [eno2](./System_Networks.md))
  * Startup the nodes and ensure that a ssh connect from the external interfaces is possible
* Check [SSH Logins](./System_Usage.md#configure-ssh-access) to
  * st01-mgmt-r01-u30
  * st01-mgmt-r01-u31
* Check [VPN Connections](./System_Usage.md#configure-vpn-access)
  * scs-manager
  * scs-manager2
* Check switches
  ```
  ./switch_ctl -s all 2>/dev/null|grep st01-sw| while read host; do echo "** $host";echo ssh ${host}-bmc "uptime"; done
  ```
* Startup Controllers (Ceph and Openstack)
  ```
  NODES="$(./server_ctl -s all 2>/dev/null|grep -- "st01-ctl")"
  ./server_ctl --power_action On $NODES
  ./server_ctl -o $NODES
  ./server_ctl --power_check $NODES
  for node in $NODES; do echo "--> $node"; ssh $node "sudo uptime"; done
  ```
* Startup Ceph and Openstack Services
  ```
  NODES="$(./server_ctl -s all 2>/dev/null|grep -- "st01-ctl"|sort -r)"
  for node in $NODES; do
    echo "--> $node";
    ssh $node "sudo systemctl enable docker.service";
    ssh $node "sudo systemctl start --all docker.service";
    ssh $node "sudo systemctl start --all osism\*";
    ssh $node "sudo systemctl start --all ceph\*";
    ssh $node "sudo systemctl start --all kolla\*";
    while ! (ssh $node sudo /usr/local/scripts/scs_check_services.sh) ; do
      echo -e "\nwaiting"; sleep 50;
    done
  done
  ```

* Startup Ceph OSDs
  ```
  NODES="$(./server_ctl -s all 2>/dev/null|grep -- "st01-stor")"
  ./server_ctl --power_action On $NODES
  ./server_ctl -o $NODES
  ./server_ctl --power_check $NODES
  for node in $NODES; do echo "--> $node"; ssh $node "sudo systemctl enable docker.service"; done
  for node in $NODES; do
    echo "--> $node";
    ssh $node "sudo systemctl enable docker.service";
    ssh $node "sudo systemctl start --all docker.service";
    ssh $node "sudo systemctl start --all osism\*";
    ssh $node "sudo systemctl start --all kolla\*";
    ssh $node "sudo systemctl start --all ceph\*"; done
    while ! (ssh $node sudo /usr/local/scripts/scs_check_services.sh) ; do
      echo -e "\nwaiting"; sleep 50;
    done
  done
  ```
* Reactivate Ceph
  ```
  ssh scs-manager
  ceph -w
  ceph osd unset noout
  ceph osd unset nobackfill
  ceph osd unset norecover
  ceph osd unset norebalance
  ceph osd unset nodown
  ceph osd unset pause
  ceph -w
  ```
  State should be **HEALTHY** now

* Local: Startup Compute Nodes with Neutron Nodes
  ```
  NODES="st01-comp-r01-u09 st01-comp-r01-u11 st01-comp-r01-u13"
  ./server_ctl --power_action On $NODES
  ./server_ctl -o $NODES
  ./server_ctl --power_check $NODES
  for node in $NODES; do
    echo "--> $node";
    ssh $node "sudo systemctl enable docker.service";
    ssh $node "sudo systemctl start --all docker.service";
    ssh $node "sudo systemctl start --all osism\*";
    ssh $node "sudo systemctl start --all ceph\*";
    ssh $node "sudo systemctl start --all kolla\*";
    while ! (ssh $node sudo /usr/local/scripts/scs_check_services.sh) ; do
      echo -e "\nwaiting"; sleep 50;
    done
  done
  ```

* Local: Startup Compute Nodes
  ```
  NODES="st01-comp-r01-u15 st01-comp-r01-u17 st01-comp-r01-u19"
  ./server_ctl --power_action On $NODES
  ./server_ctl -o $NODES
  ./server_ctl --power_check $NODES
  for node in $NODES; do
    echo "--> $node";
    ssh $node "sudo systemctl enable docker.service";
    ssh $node "sudo systemctl start --all docker.service";
    ssh $node "sudo systemctl start --all osism\*";
    ssh $node "sudo systemctl start --all ceph\*";
    ssh $node "sudo systemctl start --all kolla\*";
    while ! (ssh $node sudo /usr/local/scripts/scs_check_services.sh) ; do
      echo -e "\nwaiting"; sleep 50;
    done
  done

  ```
* Check the system, execute the [validation steps](./System_Deployment.md#step-5-validate-the-installation)
