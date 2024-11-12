# Install Cluster Stacks

## Preinstallation Steps

- Download Base VM Images

  ```sh
  osism manage image clusterapi
  ```
* Clusterstacks Bootstrap VM
  ```sh
  ./landscape_ctl --config k8s-clusterstacks.yaml \
    --create_domains k8s-clusterstacks --create_projects management --create_machines bootstrap1

  ```sh
* Create a project for the controller cluster
  ```
  ./landscape_ctl --config k8s-clusterstacks.yaml \
    --create_domains k8s-clusterstacks --create_projects controllers --create_machines none
  ```
* Check environment
  ```
  openstack domain list
  openstack project list --long
  openstack server list --all-projects --long
  ```

## Delete Installation

```sh
./landscape_ctl --config k8s-clusterstacks.yaml \
  --delete_domains k8s-clusterstacks
```

# Session 2024-11-11

## Configure VM

**/etc/docker/daemon.json**

```json
{
  "mtu": 1342
}
```

## Install Bootstrap Cluster

Use https://docs.scs.community/docs/container/components/cluster-stacks/components/cluster-stacks/providers/openstack/quickstart/ as guide, but adjust steps to use Helm charts instead -> need to be documented

- `Prerequisites` are still the same
- `Initialize the management cluster` also still the same

### Install CSO and CSPO using local Helm Charts

```sh
git clone https://github.com/SovereignCloudStack/cluster-stacks -b feat/charts
cd cluster-stacks/charts
helm upgrade -i cso -n cso-system --create-namespace ./cso --set clusterStackVariables.ociRepository=registry.scs.community/csctl-oci/openstack
helm upgrade -i cspo -n cspo-system --create-namespace ./cspo --set clusterStackVariables.ociRepository=registry.scs.community/csctl-oci/openstack
```

[Install CSP-Helper chart](https://docs.scs.community/docs/container/components/cluster-stacks/components/cluster-stacks/providers/openstack/quickstart/#deploy-csp-helper-chart) stays the same

### Create Cluster Stack

Using [this Cluster Stack](https://registry.scs.community/harbor/projects/39/repositories/openstack/artifacts-tab/artifacts/sha256:5ec408cee850ab2c1bea4ca47cb097be9af665b0a95ba15cbf914f48c68d22c2)

```yaml
apiVersion: clusterstack.x-k8s.io/v1alpha1
kind: ClusterStack
metadata:
  name: vp18-mgmt
  namespace: vp18
spec:
  provider: openstack
  name: scs
  kubernetesVersion: "1.30"
  channel: stable
  autoSubscribe: false
  providerRef:
    apiVersion: infrastructure.clusterstack.x-k8s.io/v1alpha1
    kind: OpenStackClusterStackReleaseTemplate
    name: cspotemplate
  versions:
    - v1
```

```

```
