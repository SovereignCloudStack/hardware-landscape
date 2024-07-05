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
  Include ${SCS_ENV_DIR:?}/config-snippets/ssh_config_scs_servers
  Include ${SCS_ENV_DIR:?}/config-snippets/ssh_config_scs_switches
  Include ${SCS_ENV_DIR:?}/config-snippets/ssh_config_scs_general

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
## Serial Switch Console Access

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

# Simple connection to the datacenter

Execute the following command to have access to lab networks:
```
sshuttle -r scs-manager 10.10.23.0/24 10.10.22.0/24 10.10.21.0/24
```

