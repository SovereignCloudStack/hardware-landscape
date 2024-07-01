# Runbooks of the Hardware Landscape

# Manage SSH Access and Adminstrative Permissions

* Edit [environments/configuration.yml](../environments/configuration.yml)
  * Add new users in `user_list` section
  * Actively remove users by adding them in the `user_delete
* Rollout changes 
  ```
  ssh st01-mgmt-r01-u30
  osism apply user
  osism apply operator
  ```

# Manage VPN Access

* Generate a keypair localally and add the public key 
  ```
  VPN_KEYDIR="${HOME}/.vpn/scs_hardware_landscape"
  mkdir -m 0700 -p "${VPN_KEYDIR?The wireguard keydir}"
  wg genkey | tee "${VPN_KEYDIR?}/wireguard_private.key" | wg pubkey > "${VPN_KEYDIR?}/wireguard_public.key"
  echo "${VPN_KEYDIR?}"
  cat ${VPN_KEYDIR?}/wireguard_public.key
  ```
* Edit [environments/configuration.yml](../environments/configuration.yml) in section ``wireguard_users``
  * Add username (same as github handle)
  * Add public key to user entry
* Rollout changes
  ```
  ssh st01-mgmt-r01-u30
  osism apply wireguard -l manager
  ```
* Download config from the homedir of the managers
* Add your private key
