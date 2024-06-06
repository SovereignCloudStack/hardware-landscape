# How to work with environment


* Clone the documentation
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
	Include ${SCS_ENV_DIR}/hardware-landscape/ssh/ssh_config_scs_servers
	Include ${SCS_ENV_DIR}/hardware-landscape/ssh/ssh_config_scs_switches
	Include ${SCS_ENV_DIR}/hardware-landscape/ssh/ssh_config_scs_general

	Host scs-node-*
		 ProxyJump scs-manager
     # Online needed while bootsrapping
		 # User osism

	Host scs-*
     # Your github id
		 User {GITHUB_ID}
  EOF

  ```
* Update the SSH configuration
  ```
  cd ${SCS_ENV_DIR}
  git pull
  ./switch_ctl -c all
  ./server_ctl -c all
  ```
* Login to manager
  ```
  ssh scs-manager
  ```

# Simple connection to the datacenter

```
sshuttle -r scs-manager 10.10.23.0/24
```

