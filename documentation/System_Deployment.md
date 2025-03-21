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
  git diff
  ```
* Step 3: Configure the nodes
  ```
  ./server_ctl --restore_cfg bmc all
  ```
* Step 4: Backup and check new config
  ```
  ./server_ctl --backup_cfg all
  git diff
  ```

## Deployment of the nodes

### Step 1: Initial installation of the manager


1. [Installation of the manager node](setup/Managager_Node.md)
2. Configure manager node
   * Align configuration
     (replace external with internal ip address in `ansible_host`)
     ```
     vim -d environments/manager/host_vars/st01-mgmt-r01-u30.yml ./inventory/host_vars/st01-mgmt-r01-u30/01_base.yml
     ```
   * Run Ansible on manager
     ```
     ssh st01-mgmt-r01-u30
     sudo -u dragon -i
     osism sync configuration
     osism sync inventory
     osism apply facts
     ```
3. Install Manager Infrastructure from manager
   ```
   sudo -u dragon -i
   osism apply scs_infra -l manager
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
  ssh dragon@scs-node-st01-mgmt-r01-u30
  cd /opt/configuration/misc/node-images
  make all
  ```

### Step 3: Provision / Install the node images

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
  ./server_ctl --power_action ForceOff --filter device_model=H12SSL-CT all
  ./server_ctl --install_os -w --filter device_model=H12SSL-CT all

  # Intel Compute Servers
  ./server_ctl --power_action ForceOff --filter device_model=H12SSL-NT all
  ./server_ctl --install_os -w --filter device_model=H12SSL-NT all

  # ARM Compute Servers
  TODO
  ```

### Step 4: Bootstrap the nodes

* Create and configure certificates
  (creates an configure the certificates as described in the [loadbalancer documentation](https://osism.tech/docs/guides/configuration-guide/loadbalancer))
  ```
  misc/create_certs_self_signed.sh add
  ```
* Set basic system time to prevent problems with apt and signatures
  based on a http request to www.google.com.
  (prevents problems with gpg signatures of packages)
  ```
  osism apply scs_set_time_initial -l 'all:!manager'
  ```
* Install the installation infrastructure
  ```
  osism apply scs_infra
  ```
* Execute the [bootstrap procedure](https://osism.tech/de/docs/guides/deploy-guide/bootstrap) with a configured
  layer 3 underlay before restarting the servers
  ```
  osism apply frr
  ```
* Run Basic customizations
  ```
  osism apply scs_all_nodes -l 'all:!manager'
  ```
* Check if the ntp time and the network setup is correct
  (checks pre installation conditions like proper time sync and network connectivity)
  ```
  osism apply scs_check_preinstall
  osism validate ceph-connectivity
  ```
* Reboot all hosts
  ```
  osism apply reboot -l 'all:manager' -e ireallymeanit=yes -e reboot_wait=true
  osism apply reboot -l 'all:!manager' -e ireallymeanit=yes -e reboot_wait=true
  ```

## Deploy the infrastructure services

### Step 1:

[Infrastructure](https://osism.tech/de/docs/guides/deploy-guide/services/infrastructure)
[Logging & Monitoring](https://osism.tech/de/docs/guides/deploy-guide/services/logging-monitoring)

### Step 2: Network

The OVN database is deployed to the first 3 compute nodes because the ATOM CPUs do not not support the suitable AVX instructions.

[Network](https://osism.tech/de/docs/guides/deploy-guide/services/network)


### Step 3: Logging & Monitoring

1. Follow the [Logging & Monitoring deployment](https://osism.tech/docs/guides/deploy-guide/services/logging-monitoring)
2. Deploy Scaphandre
   ```
   osism apply scaphandre
   ```

### Step 4: Ceph

For the steps described in the osd configurtion there are the following exceptions:

1. After the file generation
   Copy the generated files using the following step to the inventory:
   ```
   for filename in /tmp/st01-stor*.yml; do
     node="$(basename $filename|sed '~s,-ceph-lvm-configuration.yml,,')";
     cp -v $filename /opt/configuration/inventory/host_vars/${node}/10_ceph.yml ;
   done
   cd /opt/configuration
   git mv inventory/group_vars/ceph-resource.yml inventory/group_vars/ceph-resource.yml.disabled
   git add -A .
   git commit -m "osd-generation" -a -s
   git push
   ```
2. [Ceph](https://osism.tech/de/docs/guides/deploy-guide/services/ceph)


### Step 5: Openstack

1. Install all steps from [OpenStack](https://osism.tech/de/docs/guides/deploy-guide/services/openstack)
   except `osism apply octavia`
2. Execute the environment setup
   (There is currently a bug: #61)
   ```
   osism apply scs_landscape_setup
   ```
3. Execute Octavia Installation
   ```
   osism apply octavia
   ```

### Step 5: Validate the Installation

* Run the Postinstallation validation
  ```
  osism apply scs_check_postinstall
  ```
* Run the OSISM validations
  ```
  /opt/configuration/misc/run_validations.sh
  ```
* Use the small scenario of the next step

## Step 6: Create Test Workload

Test the deployed platform by creating some domains, projects and virtual machines.

You can use the [tiny scenario](https://github.com/SovereignCloudStack/openstack-workload-generator?tab=readme-ov-file#example-usage-a-tiny-scenario).

```
cd /home/dragon
gut clone https://github.com/SovereignCloudStack/openstack-workload-generator.git
cd openstack-workload-generator
cp /opt/configuration/environments/openstack/{secure.yml,clouds.yml} .
./openstack_workload_generator \
    --create_domains smoketest{1..2} \
    --create_projects smoketest-project{1..2} \
    --create_machines smoketest-testvm{1..2}

```
## Step 7: Run Stresstest Workload

Use the [huge stresstest scenario](https://github.com/SovereignCloudStack/openstack-workload-generator?tab=readme-ov-file#example-usage-a-huge-stresstest-scenario).
