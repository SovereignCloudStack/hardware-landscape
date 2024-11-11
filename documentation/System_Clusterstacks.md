# Install Cluster Stacks


## Preinstallation Steps

* Download Base VM Images
  ```
  osism manage image clusterapi
  ```

* Clusterstacks Bootstrap VM

  ```
  ./landscape_ctl --config k8s-clusterstacks.yaml \
    --create_domains k8s-clusterstacks --create_projects managment --create_machines bootstrap1
  ./landscape_ctl --config k8s-clusterstacks.yaml \
    --create_domains k8s-clusterstacks --create_projects controllers --create_machines none
  openstack domain list
  openstack project list --long
  openstack server list --all-projects --long
  ```

## Delete Installation

  ```
  ./landscape_ctl --config k8s-clusterstacks.yaml \
    --delete_domains k8s-clusterstacks
  ```
