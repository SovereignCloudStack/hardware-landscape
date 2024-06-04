# Deployment of the Hardware Landscape

## Deployment of the switches

## Configure hardware of the nodes

* Step 1: Make a backup of all hardware settings
  ```
  ./server_ctl --backup_cfg all
  ```
* Step 2: Template the configurations
  ```
  ./server_ctl --bmc_template all
  ./server_ctl --bmc_template st01-comp-r01-u09
  git diff
  ```
* Step 3: Configure the nodes
  ```
  ./server_ctl --restore_cfg bmc all
  ./server_ctl --restore_cfg bmc st01-comp-r01-u09
  ```

## Deployment of the nodes

### Step 1: Initial installation of the manager


1. [Installation of the manager node](setup/Managager_Node.md)
2. Configure manager node
   * Align configuration
     (replace external with internal ip address in `ansible_host`)
     ```
     vim -d environments/manager/host_vars/st01-mgmt-r01-u30.yml ./inventory/host_vars/st01-mgmt-r01-u30.yml
     ```
   * Run Ansible on manager
     ```
     ssh st01-mgmt-r01-u30
     sudo -u dragon -i
     osism apply configuration
     ```
3. Install Manager Infrastructure from manager
   ```
   sudo -u dragon -i
   osism apply manager_infra
   ```

### Step 2: Create and publish node images

* Create node node-images on manager
  ```
  st01-mgmt-r01-u30
  cd /opt/configuration/misc/node-images
  make all
  ```
* Configure  "local shell on your local system
  * Add the passwords file for BMC password data (TODO, add this later to ansible secrets) : ``secrets/server.passwords``
* Bootstrap legacy AMI BMC systems:
  (A2SDV-4C-LN8F and A2SDV-4C-LN8F, `st01-mgmt-*` and `st01-ctl`)
    1. Configure Virtual Media
      * Server: 10.10.23.254
      * Path to Image: `\media\<MODEL>.iso` 
      * User: osism
      * Password: osism
    2. Mount CDROM image
    3. Open "iKVM/HTML5" Console
    4. "Set Power Reset", select CD by using the boot menu (F11)
    5. Unmount CDROM image after first shutdown
    6. "Power up" until bootstrap installation is complete
* Bootstrap systems with latest AMI BMC
  ```
  # Storage Servers
  ./server_ctl --power_off \
    st01-stor-r01-u01 st01-stor-r01-u03 st01-stor-r01-u05 st01-stor-r01-u07
  ./server_ctl --install_os \
    st01-stor-r01-u01 st01-stor-r01-u03 st01-stor-r01-u05 st01-stor-r01-u07

  # Compute Servers
  ./server_ctl --power_off \
    st01-comp-r01-u09 st01-comp-r01-u11 st01-comp-r01-u13 st01-comp-r01-u15 st01-comp-r01-u17 st01-comp-r01-u19
  ./server_ctl --install_os \
    st01-comp-r01-u09 st01-comp-r01-u11 st01-comp-r01-u13 st01-comp-r01-u15 st01-comp-r01-u17 st01-comp-r01-u19

  # Power all servers on
  ./server_ctl --power_on all
  ```
* Bootstrap legacy ARM systems

