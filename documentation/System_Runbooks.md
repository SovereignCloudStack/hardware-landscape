# Runbooks of the Hardware Landscape

# How to get access

## Manage SSH Access and Adminstrative Permissions

1. User: Clone repository and create PR
   ```
   git clone git@github.com:SovereignCloudStack/hardware-landscape.git
   cd hardware-landscape
   ```
2. User: Edit [environments/configuration.yml](../environments/configuration.yml)
  * Create branch
  * Add new users in `user_list` section
  * Actively remove users by adding them in the `user_delete
  * Create pull request to `main` branch
3. Admin: Rollout changes
   ```
   ssh scs-manager
   osism apply user
   osism apply operator
   ```
4. User: [Configure and use SSH Access](./System_Usage.md)

## Manage VPN Access

1. User: Clone repository and create PR
   ```
   git clone git@github.com:SovereignCloudStack/hardware-landscape.git
   cd hardware-landscape
   ```
2. User: Generate a keypair localally and add the public key
   ```
   VPN_KEYDIR="${HOME}/.vpn/scs_hardware_landscape"
   mkdir -m 0700 -p "${VPN_KEYDIR?The wireguard keydir}"
   wg genkey | tee "${VPN_KEYDIR?}/wireguard_private.key" | wg pubkey > "${VPN_KEYDIR?}/wireguard_public.key"
   echo "${VPN_KEYDIR?}"
   cat ${VPN_KEYDIR?}/wireguard_public.key
   ```
3. User: Edit [../inventory/group_vars/manager_infra/00_main.yml](../inventory/group_vars/manager_infra/00_main.yml) in section ``wireguard_users``
  * Create branch
  * Add username (same as github handle)
  * Add public key to user entry
  * Remove outdated users
  * Create pull request to `main` branch
4. Admin: Rollout changes
   ```
   ssh scs-manager
   osism apply wireguard -l manager
   ```
5. User: Download config from the homedir of the managers and ad private key
   ```
   VPN_KEYDIR="${HOME}/.vpn/scs_hardware_landscape"
   scp scs-manager:wg0-*.conf ${VPN_KEYDIR?}/wg.conf
   scp scs-manager2:wg0-*.conf ${VPN_KEYDIR?}/wg2.conf
   sed -i "~s,CHANGEME.*,$(cat ${VPN_KEYDIR?}/wireguard_private.key)," "${VPN_KEYDIR?}/wg.conf" "${VPN_KEYDIR?}/wg2.conf"
   ```
6. User: Test access - start/stop first connection
   ```
   sudo apt-get install wireguard wireguard-tools # or something compareable for your system
   sudo wg-quick up "${VPN_KEYDIR?}/wg.conf"
   sudo wg-quick down "${VPN_KEYDIR?}/wg.conf"
   ```

7. User: Test access - start/stop second connection
   (You should only use one connection, the second connection is just a fallback if the first manager is not reachable)
   ```
   sudo wg-quick up "${VPN_KEYDIR?}/wg2.conf"
   sudo wg-quick down "${VPN_KEYDIR?}/wg2.conf"
   ```

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

* Shutdown Compute Nodes
  ```
  NODES="st01-comp-r01-u15 st01-comp-r01-u17 st01-comp-r01-u19"
  ./server_ctl --power_action GracefulShutdown $NODES
  ./server_ctl --power_check $NODES
  ./server_ctl --power_action ForceOff $NODES
  ```
* Shutdown Compute Nodes with Neutron Nodes
  ```
  NODES="st01-comp-r01-u09 st01-comp-r01-u11 st01-comp-r01-u13"
  ./server_ctl --power_action GracefulShutdown $NODES
  ./server_ctl --power_check $NODES
  ./server_ctl --power_action ForceOff $NODES
  ```
* Prepare Ceph for shutdown
  see http://docs-old.osism.tech/services/ceph.html#cluster-start-and-stop
  ```
  ssh scs-manager
  ceph osd set noout
  ceph osd set nobackfill
  ceph osd set norecover
  ceph osd set norebalance
  ceph osd set nodown
  ceph osd set pause

  ssh st01-ctl-r01-u27 sudo systemctl stop ceph-mgr\*.service
  ssh st01-ctl-r01-u28 sudo systemctl stop ceph-mgr\*.service
  ssh st01-ctl-r01-u29 sudo systemctl stop ceph-mgr\*.service

  ssh st01-stor-r01-u01 sudo systemctl stop ceph.target
  ssh st01-stor-r01-u03 sudo systemctl stop ceph.target
  ssh st01-stor-r01-u05 sudo systemctl stop ceph.target
  ssh st01-stor-r01-u07 sudo systemctl stop ceph.target

  ssh st01-ctl-r01-u27 sudo systemctl stop ceph.target
  ssh st01-ctl-r01-u28 sudo systemctl stop ceph.target
  ssh st01-ctl-r01-u29 sudo systemctl stop ceph.target
  ```
* Shutdown Ceph OSDs
  ```
  NODES="$(./server_ctl -s all 2>/dev/null|grep -- "st01-stor")"
  ./server_ctl --power_action GracefulShutdown $NODES
  ./server_ctl --power_check $NODES
  ./server_ctl --power_action ForceOff $NODES
  ```
* Shutdown Controllers (Ceph and Openstack)
  ```
  NODES="$(./server_ctl -s all 2>/dev/null|grep -- "st01-ctl")"
  ./server_ctl --power_action GracefulShutdown $NODES
  ./server_ctl --power_check $NODES
  ./server_ctl --power_action ForceOff $NODES
  ```
* Shutdown Switches
  ```
  ./switch_ctl -s all 2>/dev/null |while read host; do echo "** $host";ssh $host "sudo halt"; done
  ```
* Shutdown Managers
  ```
  ./server_ctl --power_action GracefulShutdown  st01-mgmt-r01-u31
  ./server_ctl --power_check $NODES st01-mgmt-r01-u31
  ./server_ctl --power_action ForceOff $NODES st01-mgmt-r01-u31

  sudo halt
  ```

