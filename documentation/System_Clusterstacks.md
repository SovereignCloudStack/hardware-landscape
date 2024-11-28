# Install Cluster Stacks

## Preinstallation Steps

* Download Base VM Images

  ```sh
  osism manage image clusterapi
  ```
* Clusterstacks Bootstrap VM
  ```sh
  WLM_CONFIG="/opt/configuration/environments/custom/roles/scs-clusterstacks/files/k8s-clusterstacks.yaml"
  WL_DOMAIN="k8s-clusterstacks-test"
  /home/dragon/openstack-workload-generator/openstack_workload_generator \
    --create_domains ${WL_DOMAIN?WL_DOMAIN} --create_projects management --create_machines bootstrap1 \
    --ansible_inventory /opt/configuration/inventory/host_vars
  ```sh
* Create a project for the controller cluster
  ```
  /home/dragon/openstack-workload-generator/openstack_workload_generator \
    --config ${WLM_CONFIG?WLM_CONFIG} \
    --create_domains ${WL_DOMAIN?WL_DOMAIN} --create_projects controllers --create_machines none \
    --ansible_inventory /opt/configuration/inventory/host_vars
  ```
* Check environment
  ```
  openstack domain list
  openstack project list --long
  openstack server list --all-projects --long
  ssh ubuntu@floating-ip
  ```
* Install clusterstacks
  ```
  osism apply scs_clusterstacks
  ```

## Delete Installation

```sh
/home/dragon/openstack-workload-generator/openstack_workload_generator \
    --config ${WLM_CONFIG?WLM_CONFIG}  --delete_domains ${WL_DOMAIN?WL_DOMAIN}
```
