# Runbooks of the Hardware Landscape

# How to get access

# Manage SSH Access and Adminstrative Permissions

1. Clone repository and create PR
2. User: Edit [environments/configuration.yml](../environments/configuration.yml)
  * Add new users in `user_list` section
  * Actively remove users by adding them in the `user_delete
3. Admin: Rollout changes
   ```
   ssh scs-manager
   osism apply user
   osism apply operator
   ```

# Manage VPN Access

1. User: Clone repository and create PR
2. User: Generate a keypair localally and add the public key
   ```
   VPN_KEYDIR="${HOME}/.vpn/scs_hardware_landscape"
   mkdir -m 0700 -p "${VPN_KEYDIR?The wireguard keydir}"
   wg genkey | tee "${VPN_KEYDIR?}/wireguard_private.key" | wg pubkey > "${VPN_KEYDIR?}/wireguard_public.key"
   echo "${VPN_KEYDIR?}"
   cat ${VPN_KEYDIR?}/wireguard_public.key
   ```
3. User: Edit [../inventory/group_vars/wireguard.yml](../inventory/group_vars/wireguard.yml) in section ``wireguard_users``
  * Add username (same as github handle)
  * Add public key to user entry
  * Remove outdated users
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
6. User: Test access - start/stop connection
   ```
   sudo apt-get install wireguard wireguard-tools # or something compareable for your system
   sudo wg-quick up "${VPN_KEYDIR?}/wg.conf"
   sudo wg-quick down "${VPN_KEYDIR?}/wg.conf"
   sudo wg-quick up "${VPN_KEYDIR?}/wg2.conf"
   sudo wg-quick down "${VPN_KEYDIR?}/wg2.conf"
   ```

