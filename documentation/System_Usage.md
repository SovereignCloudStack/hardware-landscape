# How to work with environment

## Configure SSH Access

The **user** and **admin** annotation describes who is capable to perform that task.

The following section describes how to include config snippets in the ssh configuration
of your local system to simplify access to systems of the vp18 hardware landscape.

1. **User**: Clone the repository
   ```
   cd <your-sourcecode-dir>
   git clone git@github.com:SovereignCloudStack/hardware-landscape.git
   cd hardware-landscape
   SCS_ENV_DIR="$(pwd)"
   GITHUB_ID="scoopex" # Replace that by your own ID
   ```
2. **User**: [Add your user](./System_Runbooks.md) if not already added and wait until some with admin privileges has rolled out your keys.
3. **User**: Add this snippet to your SSH configuration:
   ```
   cat >> ~/.ssh/config <<EOF
   Include ${SCS_ENV_DIR:?}/config-snippets/ssh_config_scs_servers
   Include ${SCS_ENV_DIR:?}/config-snippets/ssh_config_scs_switches
   Include ${SCS_ENV_DIR:?}/config-snippets/ssh_config_scs_general

   Host scs-* st01-* !scs-manager !scs-manager1 !scs-manager2
      ProxyJump scs-manager
      # Your github id, use "osism" or "dragon" when your are in the
      # installation process
      User ${GITHUB_ID:?}

   Host scs-manager scs-manager1 scs-manager2
      # Your github id, use "osism" or "dragon" when your are in the
      # installation process
      User ${GITHUB_ID:?}

   EOF

   ```
4. **User**: Login to manager
   ```
   ssh scs-manager
   ```
5. **User**: Login to systems directly from your workstation
   ```
   ssh scs-<TAB><TAB>
   ```

The hardware landscape setup is deployed to provide the possibility for multi user usage.
Users login with their personal account and should be capable to perform all needed operations
with docker, the osism and the hardware landscape tooling.

In the login process on the systems the `/usr/local/scripts/scs_profile.sh` is executed, to
provide a convenient and standardized environment.
Please use that profile but at least use the `umask 0007`

## Configure VPN Access

The **user** and **admin** annotation describes who is capable to perform that task.

1. **User**: Clone repository and create PR
   ```
   git clone git@github.com:SovereignCloudStack/hardware-landscape.git
   cd hardware-landscape
   ```
2. **User**: Generate a keypair localally and add the public key
   ```
   VPN_KEYDIR="${HOME}/.vpn/scs_hardware_landscape"
   mkdir -m 0700 -p "${VPN_KEYDIR?The wireguard keydir}"
   wg genkey | tee "${VPN_KEYDIR?}/wireguard_private.key" | wg pubkey > "${VPN_KEYDIR?}/wireguard_public.key"
   echo "${VPN_KEYDIR?}"
   cat ${VPN_KEYDIR?}/wireguard_public.key
   ```
3. **User**: Edit [../inventory/group_vars/manager_infra/00_main.yml](../inventory/group_vars/manager_infra/00_main.yml) in section ``wireguard_users``
  * Create branch
  * Add username (same as github handle)
  * Add public key to user entry
  * Remove outdated users
  * Create pull request to `main` branch
4. **Admin**: Rollout changes
   ```
   ssh scs-manager
   osism apply wireguard -l manager
   ```
5. **User**: Download config from the homedir of the managers and ad private key
   ```
   VPN_KEYDIR="${HOME}/.vpn/scs_hardware_landscape"
   scp scs-manager:wg0-*.conf ${VPN_KEYDIR?}/wg.conf
   scp scs-manager2:wg0-*.conf ${VPN_KEYDIR?}/wg2.conf
   sed -i "~s,CHANGEME.*,$(cat ${VPN_KEYDIR?}/wireguard_private.key)," "${VPN_KEYDIR?}/wg.conf" "${VPN_KEYDIR?}/wg2.conf"
   ```
6. **User**: Test access - start/stop first connection
   ```
   sudo apt-get install wireguard wireguard-tools # or something compareable for your system
   sudo wg-quick up "${VPN_KEYDIR?}/wg.conf"
   sudo wg-quick down "${VPN_KEYDIR?}/wg.conf"
   ```

7. **User**: Test access - start/stop second connection
   (You should only use one connection, the second connection is just a fallback if the first manager is not reachable)
   ```
   sudo wg-quick up "${VPN_KEYDIR?}/wg2.conf"
   sudo wg-quick down "${VPN_KEYDIR?}/wg2.conf"
   ```


## Update the SSH configuration

   This fetches host information from the documentation in [documentation/devices](./devices) and creates new ssh config snippets
   ```
   cd ${SCS_ENV_DIR:?}
   git pull
   ./switch_ctl -c all
   ./server_ctl -c all
   ```


## Configure the Ansible vault password file

For accessing the system from your local workstation, it is neccessary to configure the Ansible vault password locally.

This is needed for reading encrypted ansible files and for getting BMC passwords.

```
ssh scs-manager "docker exec osism-ansible /ansible-vault.py" > secrets/vaultpass
```

## Serial Switch Console Access

* Login to first manager
  ```
  ssh scs-manager
  ```
* Attach to a running screen session which provides access to the ttypS0..ttySX interfaces
  or create automatically a new one
  ```
  scs_serial_access
  ```
* Restart all sessions
  1. Attach to running session
     ```
     scs_serial_access
     ```
  2. Terminate sessions by STRG+y :quit
  3. Restart terminals
     ```
     scs_serial_access
     ```
* Review console output
  see /var/log/screen

* Screen Usage :
  - 'CTLR + y d'
     leave the session
  - 'CTLR + y, "'
     select your terminal
  - 'CTLR + y, :quit' 
     terminate screen entirely
  - 'CTLR + y, :break' 
     send a break signal
      - Use the screen command 
         press 'STRG+y' 
         send a break signal: ':break<ENTER>'
      - Hit the sysrq char "b" multiple times
      - Watch the hardware booting :-)


# Miscellanious Procedures

## Permission Problems

The hardware landscape setup is deployed to provide the possibility for multi user usage.
Users login with their personal account and should be capable to perform all needed operations
with docker, the osism and the hardware landscape tooling.

In the login process on the systems the `/usr/local/scripts/scs_profile.sh` is executed, to
provide a convenient and standardized environment.
(this also sets `umask 00007`).

In some cases permission problems may appear, this can be fixed by executing.
```
$ scs_fix_permissions.sh
+ fix_perm /usr/local/scripts
+ sudo find /usr/local/scripts -type d -exec chmod 770 '{}' +
+ sudo find /usr/local/scripts -type f -exec chmod 660 '{}' +
+ sudo find /usr/local/scripts -type f '(' -name '*.sh' -or -name '*_ctl' -or -path '*/venv/bin/*' -or -path '*/.venv/bin/*' ')' -exec chmod 770 '{}' +
+ sudo find /usr/local/scripts -exec chown dragon:dragon '{}' +
+ fix_perm /opt/configuration
+ sudo find /opt/configuration -type d -exec chmod 770 '{}' +
+ sudo find /opt/configuration -type f -exec chmod 660 '{}' +
+ sudo find /opt/configuration -type f '(' -name '*.sh' -or -name '*_ctl' -or -path '*/venv/bin/*' -or -path '*/.venv/bin/*' ')' -exec chmod 770 '{}' +
+ sudo find /opt/configuration -exec chown dragon:dragon '{}' +
+ git config --global --add safe.directory /opt/configuration
```

## Update ansible inventory data

The following section describes how to regenerate  inventory files 
based on the documentation in [documentation/devices](./devices).

* Enter configuration directory and verify that there are no open changes
  ```
  cd <your-sourcecode-dir>/hardware-landscape
  git stash
  git checkout -b "update-inventory-files"
  ```
* Regenerate inventory files
  ```
  ./server_ctl --ansible all
  ./switch_ctl --ansible all
  ```
* Check changes
  ```
  git diff
  ```
* Merge changes
  ```
  git commit ...
  git push
  ...
  ```


## Simple connection to the datacenter

Execute the following command to have access to lab networks:
```
sshuttle -r scs-manager 10.10.23.0/24 10.10.22.0/24 10.10.21.0/24
```

