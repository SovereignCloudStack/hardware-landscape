# How to work with environment

The following section describes how to include config snippets in the ssh configuration
of your local system to simplify access to systems of the vp18 hardware landscape.

* Clone the repository
  ```
  cd <your-sourcecode-dir>
  git clone git@github.com:SovereignCloudStack/hardware-landscape.git
  cd hardware-landscape
  SCS_ENV_DIR="$(pwd)"
  GITHUB_ID="scoopex"
  ```
* Add this snippet to your SSH configuration:
  ```
  cat >> ~/.ssh/config <<EOF
  Include ${SCS_ENV_DIR:?}/hardware-landscape/config-snippets/ssh_config_scs_servers
  Include ${SCS_ENV_DIR:?}/hardware-landscape/config-snippets/ssh_config_scs_switches
  Include ${SCS_ENV_DIR:?}/hardware-landscape/config-snippets/ssh_config_scs_general

  Host scs-node-*
      ProxyJump scs-manager
      # User "osism" is only needed while bootstrapping
      # User osism

  Host scs-*
      # Your github id
      User ${GITHUB_ID:?}
  EOF

  ```
* Update the SSH configuration
  (this fetches host information from the documentation in [documentation/devices](./devices) and creates new ssh config snippets)
  ```
  cd ${SCS_ENV_DIR:?}
  git pull
  ./switch_ctl -c all
  ./server_ctl -c all
  ```
* Login to manager
  ```
  ssh scs-manager
  ```
* Login to systems
  ```
  ssh scs-<TAB><TAB>
  ```

# Update ansible inventory data

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

# Simple connection to the datacenter

Execute the following command to have access to lab networks:
```
sshuttle -r scs-manager 10.10.23.0/24 10.10.22.0/24 10.10.21.0/24
```

