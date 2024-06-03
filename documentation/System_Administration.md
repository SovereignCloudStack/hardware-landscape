# Administration of the Hardware Landscape

## Installing the entire system



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
3. Install Manager Infrastructure
   ```
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
* Bootstrap legacy ARM systems

## Runbooks

### Manage Access to Landscape

* Edit [environments/configuration.yml](../environments/configuration.yml)
* Rollout changes
  ```
  osism apply user
  osism apply operator
  ```
