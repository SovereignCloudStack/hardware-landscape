# Administration of the Hardware Landscape

## Initial installation

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
1. [Install a proxy](https://osism.tech/docs/guides/configuration-guide/proxy)

## Manager Access

```

```
