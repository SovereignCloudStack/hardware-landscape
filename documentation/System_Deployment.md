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

We had the romantic idea that installing supermico hardware using the redfish api would be a good idea.

Although we only have a few systems, it would have been great to be able to reinstall them automatically and with little effort
because this is a testlab environment.

Unfortunately, Supermicro is causing us unnecessary problems at various levels:

- it is necessary to buy a BMC license to be able to automate the system at all (which surprises us in 2024 if the systems are intended for use in the data center)
- we have three generations of systems in use here, these are automated in different ways, but some features are also missing in new generations (AMI BMC 04.0, AMI BMC 01.01.10, OpenBMC 51.02.13.00)
- various functions such as setting the next boot device do not work or work only on specific devices, although the Redfish API accepts the setting without complaint
- there are no usable or clearly understandable API specifications as is typically known from systems that use OpenAPI
- The Redfish API realized by Supermicro is simply a rather cumbersome API
- The systems reconfigure their boot order independently, the exact meaning behind this is not clear to us and we have not found a way to change this behavior
- ...

We may not know all the facts. Perhaps someone has good ideas or better background knowledge.
Please just add issues to this project with hints or directly [contact me](https://scs.community/de/schoechlin)


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
  (Just press F11 at boot to select the virtual CDROM as boot device, unfortunately Supermicro ignores the setting for the next boot device.)
  ```
  # Storage Servers
  ./server_ctl --power_off --filter device_model=H12SSL-CT all
  ./server_ctl --install_os -w --filter device_model=H12SSL-CT all

  # Intel Compute Servers
  ./server_ctl --power_off --filter device_model=H12SSL-NT all
  ./server_ctl --install_os -w --filter device_model=H12SSL-NT all

  # ARM Compute Servers
  ```
* Bootstrap legacy ARM systems
  TODO