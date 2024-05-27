# Administration of the Hardware Landscape

## Installing the entire system

### Step 0: Initial installation

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

## Runbooks

### Manage Access to Landscape

* Edit [environments/configuration.yml](../environments/configuration.yml)
* Rollout changes
  ```
  osism apply user
  osism apply operator
  ```
