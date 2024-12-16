# OVN BGP Agent in Kolla-Ansible for scalability and cloud interconnect deployments

## Test deployment of OVN BGP Agent in Kolla-Ansible
This part is a quick how-to for setting up OVN BGP Agent in Kolla-ansible.
There's an existing [PR](https://review.opendev.org/c/openstack/kolla-ansible/+/891622) in kolla-ansible upstream, however, it does not work properly. To fix the issues, a [PR in kolla-ansible fork](https://github.com/SovereignCloudStack/kolla-ansible/pull/5) and a [PR in kolla fork](https://github.com/SovereignCloudStack/kolla-ansible/pull/2) have been created in an attempt to fix the issues.

I got all containers running, however they do not seem to activate  (see below)

### Steps
- Set up a functional test environment, such as an OSISM [test environment](https://osism.tech/docs/guides/deploy-guide/examples/) like `Testbed` or `Cloud-in-a-Box`. Alternatively, you can streamline test environment creation using the [kolla-builder](https://github.com/SovereignCloudStack/kolla-builder) project, which this tutorial will demonstrate.

 - If you use kolla-builder, you need to checkout a dev branch `ovn-bgp-agent-deployment`
 ```bash
 git fetch origin ovn-bgp-agent-deployment:ovn-bgp-agent-deployment
 git checkout ovn-bgp-agent-deployment
 ```
 - Use the following variable file with kolla-builder
```yaml
inventory_name: "ovn-bgp"
image_pool: "/home/matus/pool"
image_path: "{{ image_pool }}/kolla-image.qcow2"
ara_enable: false
is_remote: false
python_bin_path: "/home/matus/scs/kolla-venv/bin"
# Use different CIDRs and virbrX interfaces if
# the provided ones are already in use
network_ssh: "kolla-ssh-bgp-flat"
network_openstack: "kolla-openstack-bgp-flat"
network_neutron: "kolla-neutron-bgp-flat"
network_ssh_ip: "192.168.122.1"
network_openstack_ip: "192.168.123.0"
network_neutron_ip: "192.168.100.0"
network_ssh_bridge: virbr0
network_openstack_bridge: virbr1
network_neutron_bridge: virbr2
create_networks: true
kolla_internal_vip_address: "192.168.123.200"
git_patch_kolla: true
git_branch: "ovn-bgp-agent"
git_patches: []
kolla_ssh_key: "{{ lookup('ansible.builtin.env', 'HOME') }}/.ssh/id_kolla"
ssh_config: "ssh_config"
globals_file: user-globals/ovn-bgp.yml
kolla_source_local_path: "<path to kolla ansible source code>"
is_aio: true
node_name: "kolla-ovn-bgp-flat"
ram_size: 10000
cpu_count: 12

```
- Clone  [kolla fork](https://github.com/SovereignCloudStack/kolla)
```
git clone git@github.com:SovereignCloudStack/kolla.git
```
>Note: It is recommended to follow the steps for building Kolla images on the all-in-one VM created by kolla-builder, rather than on your local machine, to simplify the deployment process.
>- run `./pre-deploy` script on the VM (this will install docker)
>- Repeat the steps, excluding the image-pushing step, as the images are already available

to simplyfy
- Checkout `ovn-bgp-agent` branch in  kolla
```>Note: as said above, skip this step if you built your images on kolla-builder all-in-one VM
cd kolla
git fetch origin ovn-bgp-agent:ovn-bgp-agent
git checkout ovn-bgp-agent
```
- Install kolla (edit mode is recommended)
```
# in kolla directory
pip install -e .
```
- Build images
```
kolla-build ovn-bgp-agent frr neutron horizon
```
- Get images tag
```
dokcer image ls
# EXAMPLE OUTPUT
REPOSITORY                                          TAG              IMAGE ID       CREATED        SIZE
kolla/neutron-mlnx-agent                            17.1.0           862918488114   11 days ago    1.58GB
kolla/neutron-l3-agent                              17.1.0           e908f72c8a66   11 days ago    1.56GB
kolla/neutron-linuxbridge-agent                     17.1.0           2368a2de4cba   11 days ago    1.53GB
kolla/neutron-infoblox-ipam-agent                   17.1.0           1a91373e9e5a   11 days ago    1.54GB
kolla/neutron-server                                17.1.0           52f069a2025a   11 days ago    1.54GB
kolla/neutron-bgp-dragent                           17.1.0           9a52fcab6090   11 days ago    1.53GB
kolla/neutron-sriov-agent                           17.1.0           d10be7b0502f   11 days ago    1.53GB
kolla/neutron-openvswitch-agent                     17.1.0           7612f83e42e0   11 days ago    1.53GB
kolla/neutron-dhcp-agent                            17.1.0           ada8ead6a695   11 days ago    1.53GB
kolla/neutron-metering-agent                        17.1.0           887841baf635   11 days ago    1.53GB
kolla/neutron-metadata-agent                        17.1.0           f9f6e4188dbd   11 days ago    1.53GB
kolla/neutron-ovn-agent                             17.1.0           c69e3b9a0ecc   11 days ago    1.53GB
kolla/ironic-neutron-agent                          17.1.0           7c7d9e0f4cac   11 days ago    1.53GB
kolla/neutron-base                                  17.1.0           0bb7236a857f   11 days ago    1.53GB
kolla/openstack-base                                17.1.0           a498ab05494c   11 days ago    1.17GB
kolla/horizon                                       17.1.0           c694f5bda748   12 days ago    1.4GB
kolla/ovn-bgp-agent                                 17.1.0           822880a9ec91   12 days ago    1.58GB
kolla/frr                                           17.1.0           8b6a4226d03e   12 days ago    672MB
kolla/base                                          17.1.0           cbdec5ad8b29   12 days ago    631MB
```

- Push images
```
# Example commands
docker image tag kolla/neutron-server:17.1.0  registry-host:5000/myadmin/kolla/neutron-server:latest
docker image push registry-host:5000/myadmin/kolla/neutron-server:latest
# Do this for every image that was built
```
>Note: as said above, skip this step if you built your images on kolla-builder all-in-one VM

- With your images ready you can clone [kolla ansible fork](https://github.com/SovereignCloudStack/kolla-ansible)
```
git clone --branch ovn-bgp-agent git@github.com:SovereignCloudStack/kolla-ansible.git
```
- Checkout `ovn-bgp-agent` for kolla-ansible fork
```
cd kolla-ansible
git fetch origin ovn-bgp-agent:ovn-bgp-agent
git checkout ovn-bgp-agent
```
- If you used kolla builder with locally built images add this to your `globals.yaml`
```yaml
# Use only with kolla-builder if you built your images on the VM
docker_tag: "0.1.0" # Replace with your images tag
frr_image_full: "kolla/frr:{{ docker_tag }}"
ovn_bgp_agent_image_full: "kolla/ovn-bgp-agent:{{ docker_tag }}"
horizon_image_full: "kolla/horizon:{{ docker_tag }}"
neutron_server_image_full: "kolla/neutron-server:{{ docker_tag }}"
neutron_metadata_agent_image_full: "kolla/neutron-metadata-agent:{{ docker_tag }}"
####
```

- It is also recommended,however not necessary, to clone ovn-bgp-agent and mount it to containers. This way it is easier
to debug the agent. If you use kolla builder you can do this by adding the following to your variables file. If you use other environment, make sure the source code path is accessible by ovn-bgp-agent container
```yaml
additional_uploads_deploy_node:
- "<path to ovn bgp agent source>"
additional_upload_node_path: "/home/kolla"
# This is important for
additional_upload_mode: "0777"
```
- Then mount the source code by adding this to `globals.yml`
```yaml
default_extra_volumes:
- "/home/kolla/ovn-bgp-agent/ovn_bgp_agent:/var/lib/kolla/venv/lib/python3.9/site-packages/ovn_bgp_agent"
```

## Example deployments

### NB/SB Driver BGP advertising

#### Steps

- Spawn a test VM with `frr` installed `sudo apt install frr` configure bgp peering
```
frr version 9.1.2
frr defaults traditional
hostname <your VM hostname>
log file /var/log/frr/frr.log
!
router bgp 65001
 bgp router-id 1.1.1.0
 bgp log-neighbor-changes
 no bgp ebgp-requires-policy
 no bgp default ipv4-unicast
 bgp graceful-shutdown
 neighbor kolla peer-group
 neighbor kolla remote-as 65001
 neighbor kolla remote-as internal
 neighbor <INTERFACE THAT IS ON THE SAME NETWORK AS KOLLA> interface peer-group kolla
 neighbor <IP ADRESS OF KOLLA AIO VM> peer-group kolla
 !
 address-family ipv4 unicast
  neighbor kolla activate
 exit-address-family
 !
 address-family ipv6 unicast
  neighbor kolla activate
 exit-address-family
exit
```
- Deploy kolla-ansible **without** OVN BGP agent on. This will create necessary to create ovs bridges.
- For this we are going to use `underlay` exposing method, which requires `br-ex` interface to be up.
```bash
sudo ip l set br-ex up
```
- Add a loopback ip to the `br-ex` interface
```bash
sudo ip a add 1.1.1.1/32 dev br-ex
```
- Add the following to your `globals.yaml`
```yaml
enable_ovn_bgp_agent: "yes"

ovn_bgp_agent_driver: "ovn_bgp_driver"
# for nb driver
# ovn_bgp_agent_driver: "nb_ovn_bgp_driver"
# NOTE: currently didn't manage to run nb_driver in my test environment
ovn_bgp_agent_exposing_method: "underlay"
neutron_plugin_agent: "ovn"
bgp_expose_tenant_networks: "yes"
bgp_local_asn: "64999"
bgp_loopback_ip: "172.30.1.1"
# Ip of a machine you want to advertise bgp routes to
frr_neighbor_ip: "<IP ADRESS OF TEST VM>"
```
- Deploy kolla-ansible again, with new globals.
```bash
kolla-ansible -i all-in-one deploy --tags ovn-bgp-agent,frr
```
- New interfaces will be added  `bgp-vrf` and `bgp-nic`
- Adding new floating IPs, rounters or VMs to provider network will expose them by adding them to `bgp-nic`
```bash
ip a show bgp-nic
# Example output
9: bgp-nic: <BROADCAST,NOARP,UP,LOWER_UP> mtu 1500 qdisc noqueue master bgp-vrf state UNKNOWN group default qlen 1000
    link/ether 16:23:48:49:bb:a6 brd ff:ff:ff:ff:ff:ff
    inet 192.168.100.186/32 scope global bgp-nic
       valid_lft forever preferred_lft forever
    inet 192.168.100.194/32 scope global bgp-nic
       valid_lft forever preferred_lft forever
    inet 192.168.100.187/32 scope global bgp-nic
       valid_lft forever preferred_lft forever
```

### Notes/TODO

- There seems to be an error in ovn-bgp-agent, it's described in this [launchpad](https://lists.launchpad.net/yahoo-eng-team/msg94358.html)

    - This error can be avoided but it requires some hacking
    - it seems that the external MAC is in `external_ids` field
    ```python
    allowed_ext_ips = [],
    exempted_ext_ips = [],
    external_ids = {
        'neutron:fip_external_mac': 'fa:16:3e:36:86:20',
        'neutron:fip_id': '3a329994-10bf-4631-bb0f-7ad5a71a93f9',
        'neutron:fip_network_id': 'b0d4aec5-6a4b-45fc-a530-f7c048cfc4ae',
        'neutron:fip_port_id': '9daa4dac-f9ec-44a5-b8e1-6455fca554ac',
        'neutron:revision_number': '2',
        'neutron:router_name': 'neutron-ef88cdb6-500e-46ac-afbc-6f04d5d25656'
    },
    external_ip = 192.168.100.182,
    external_mac = [],
    external_port_range = '',
    gateway_port = [<ovs.db.idl.Row object at 0x7f3c0647a0d0>],
    logical_ip = 10.0.0.62,
    logical_port = ['9daa4dac-f9ec-44a5-b8e1-6455fca554ac'],
    options = {},
    type = dnat_and_snat
    ```
    - Maybe it's some wrong setting in neutron
    - Anyway, a patch like this can be made
    ```python
        def get_port_external_ip_and_ls(self, port):
        nat_entry = self.nb_idl.get_nat_by_logical_port(port)
        if not nat_entry:
            return None, None, None
        net_id = nat_entry.external_ids.get(constants.OVN_FIP_NET_EXT_ID_KEY)
        # Add a try block
        try:
            mac = nat_entry.external_mac[0]
        except IndexError:
            mac = nat_entry.external_ids['neutron:fip_external_mac']
        if not net_id:
            return nat_entry.external_ip,mac, None
        else:
            ls_name = "neutron-{}".format(net_id)
            return nat_entry.external_ip, mac , ls_name
    ```
- Underlay exposed ips are not reachable (cannot ssh into instances) when using nb_driver. It might be due to wrong OVN configuration reffer to this note
>NOTE:
As we also want to be able to expose VM connected to tenant networks (when expose_tenant_networks or `expose_ipv6_gua_tenant_networks` configuration options are enabled), there is a need to expose the Neutron router gateway port (cr-lrp on OVN) so that the traffic to VMs in tenant networks is injected into OVN overlay through the node that is hosting that port.
## Cloud connectivity POC deployment
In this section we will deploy two Openstack-Kolla clouds using Kolla-Builder and connect them through BGP (TODO: EVPN) so that openstack instances on tennant networks can ping each other without using public FIP

### Dependencies
For this POC deployment, we need draft/development branches/forks from several repositories.
It's recommended you clone and fetch them before setting up your cloud(s). 
```bash
# Kolla builder
git clone https://github.com/SovereignCloudStack/kolla-builder.git
cd kolla-builder
git fetch origin ovn-bgp-agent-deployment:ovn-bgp-agent-deployment
git checkout ovn-bgp-agent-deployment
cd ..
# Kolla
git clone https://github.com/SovereignCloudStack/kolla.git
cd kolla
git fetch origin ovn-bgp-agent:ovn-bgp-agent
git checkout ovn-bgp-agent
cd ..
# Kolla-ansible
git clone https://github.com/SovereignCloudStack/kolla-ansible.git
cd kolla-ansible
git fetch origin ovn-bgp-agent:ovn-bgp-agent
git checkout ovn-bgp-agent
cd ..
```

### Remote machine
Setup a remote machine. Look into kolla-builder [README](https://github.com/SovereignCloudStack/kolla-builder/tree/ovn-bgp-agent-deployment) and install all the dependencies listed for your remote machine.

Go to your kolla-builder directory and edit `remote` file. Add IP of your server and your ssh, e.g.
```
[remote]
213.131.230.38  ansible_ssh_user=ubuntu ansible_become=True ansible_private_key_file=/home/matus/.ssh/id_rsa
```

### Spawning cloud 1
Create a variables file e.g. `user/ovn-bgp.yml` and globals file. `kolla-files/user-globals/ovn-bgp.yml`

- `user/ovn-bgp.yml`
```yaml

inventory_name: "ovn-bgp-multinode"
image_pool: "/var/lib/libvirt/images"
image_path: "{{ image_pool }}/kolla-image.qcow2"
ara_enable: false
is_remote: true
remote_image_pool: "/var/lib/libvirt/images"
# SSH key for the remote host
proxy_server_private_key: "{{ lookup('ansible.builtin.env', 'HOME') }}/.ssh/id_rsa"


## NETWORK
network_ssh: "kolla-ssh-bgp"
network_openstack: "kolla-openstack-bgp"
network_neutron: "kolla-neutron-bgp"

network_ssh_ip: "192.168.122.1"
network_openstack_ip: "192.168.123.0"
network_neutron_ip: "192.168.100.0"


network_ssh_bridge: virbr0
network_openstack_bridge: virbr2
network_neutron_bridge: virbr3

create_networks: true
destroy_networks: true

kolla_internal_vip_address: "192.168.123.200"
git_patch_kolla: true


git_branch: "ovn-bgp-agent"

git_patches: []
kolla_ssh_key: "{{ lookup('ansible.builtin.env', 'HOME') }}/.ssh/id_kolla"
globals_file: user-globals/ovn-bgp.yml
kolla_source_local_path: "../kolla-ansible"


is_aio: false

default_cpu: 12
default_ram: 1024
default_disksize: 25
nodes:
  - name: "kolla-ovn-bgp-control-01"
    control: true
    storage: true
    monitoring: true
    network: false
    compute: true
    ram_size: 8192

  - name: "kolla-ovn-bgp-network-01"
    network: true
    ram_size: 4096

  - name: "kolla-ovn-bgp-network-02"
    network: true
    ram_size: 4096

  - name: "kolla-ovn-bgp-deployment"
    deployment: true
    ram_size: 1024
```
- `kolla-files/user-globals/ovn-bgp.yml`
```yaml
enable_ovn_bgp_agent: "yes"
ovn_bgp_agent_driver: "ovn_bgp_driver"
ovn_bgp_agent_exposing_method: "underlay"

neutron_plugin_agent: ovn

docker_tag: "0.0.1"
frr_image_full: "{{docker_registry}}/kolla/frr:{{ docker_tag }}"
ovn_bgp_agent_image_full: "{{docker_registry}}/kolla/ovn-bgp-agent:{{ docker_tag }}"
horizon_image_full: "{{docker_registry}}/kolla/horizon:{{ docker_tag }}"
neutron_server_image_full: "{{docker_registry}}/kolla/neutron-server:{{ docker_tag }}"
neutron_metadata_agent_image_full: "{{docker_registry}}/kolla/neutron-metadata-agent:{{ docker_tag }}"
bgp_local_asn: "65001"
bgp_loopback_ip: "1.1.1.1"
bgp_expose_tenant_networks: "yes"
require_snat_disabled_for_tenant_networks: "no"
enable_neutron_bgpvpn: "no"
neutron_dev_mode: "no"
neutron_dev_repos_pull: "no"
frr_neighbor_interface: "enp1s0"
frr_neighbor_ips: []
docker_registry: "192.168.122.254:4999"
docker_registry_insecure: "yes"
```
- Spawn and prepare the cloud with
```bash
./builder -r spawn user/ovn-bgp.yml && ./builder -r prepare user/ovn-bgp.yml
```
### Setting up Docker registry
In this section, we will create a docker registry. Because it's not documented anywhere, we will provide step by step guide. Assume we did the previous steps and we have libvirt VMs running on our remote server as well as cloned kolla and kolla-ansible directories with `ovn-bgp-agent` branches checked out.

We will use our remote server that we are using to host the libvirt VMs
- Create archive of Kolla
```bash
# in the their respective directories
tar -czvf kolla.tgz kolla/
```
- Copy them to remote server. You can use `kolla-builder/ssh_config` to simplify
```bash
scp -F kolla-builder/ssh_config kolla.tgz  kolla-proxy-jump:
```
- SSH to the remote
```bash
ssh -F kolla-builder/ssh_config kolla-proxy-jump
```
- Unpack Kolla
```
tar -xzvf kolla.tgz
```

- Create a venv
```bash
sudo apt update
sudo apt install python3-venv
python3 -m venv myenv
source myenv/bin/activate
```
- Install kolla (edit mode recommended)
```bash
pip install -e ./kolla
```
- Install Kolla-ansible
```bash
# Dependencies
sudo apt install git python3-dev libffi-dev gcc libssl-dev
pip install -U pip
pip install 'ansible-core>=2.16,<2.17.99'
pip install docker
sudo apt install build-essential libdbus-glib-1-dev libgirepository1.0-dev
pip install dbus-python
# Install Kolla-ansible from master
pip install git+https://opendev.org/openstack/kolla-ansible@master
# Create configuration directory
sudo mkdir -p /etc/kolla
sudo chown $USER:$USER /etc/kolla
# Move example config files
cp -r myenv/share/kolla-ansible/etc_examples/kolla/* /etc/kolla
cp myenv/share/kolla-ansible/ansible/inventory/all-in-one .
```

- Edit `/etc/kolla/globals.yaml` and edit `network_interface` and `neutron_external_interface` to be an existing physical network interface. We are not going to use it, it is just to bypass prechecks.
```yaml
network_interface: "ens3"
neutron_external_interface: "ens3"
neutron_plugin_agent: "ovn"
```
- Get docker, using the script
```bash
curl -fsSL https://get.docker.com | sudo sh
```

- Add your IP on the network you will use to SSH into your Kolla nodes to the insecure registries.
```bash
echo '{"insecure-registries" : ["192.168.122.254:4999"]}' | sudo tee /etc/docker/daemon.json 
```
- Restart Docker engine
```bash
sudo systemctl restart docker
```
- Start the registry. Use different port that 5000, because this port is used by keystone.
```bash
docker run -d -p 4999:5000 registry:2
```
- Install additional Kolla-ansible dependencies
```bash
kolla-ansible  install-deps
```
- Pull Kolla images
```bash
kolla-ansible pull -i all-in-one
```

- Build images related to ovn-bgp-agent
```bash
kolla-build --tag 0.0.1 frr ovn-bgp-agent neutron-server horizon
```

- Use the following script to push all (official Kolla and built images ) to your registry
```bash
#!/bin/bash
DOCKER_REGISTRY="192.168.122.254:4999"
docker images | grep -v $DOCKER_REGISTRY | awk '{print $1,$2}' | while read -r image tag; do
    new_image_name=${image#"quay.io/"}
    docker tag ${image}:${tag} "$DOCKER_REGISTRY"/${new_image_name}:${tag}
    docker push $DOCKER_REGISTRY/${new_image_name}:${tag}
done
```
### Deploy Cloud 1
- Exit the remote machine and SSH into deploy node
```bash
ssh -F kolla-builder/ssh_config kolla-ovn-bgp-deployment
```

- Run the deploy script. This will deploy Openstack-Kolla as well as ovn-bgp-agent and creates demo resources

- When the deploy script finishes, on another terminal SSH to one of the network nodes.
```bash
ssh -F kolla-builder/ssh_config kolla-ovn-bgp-network-01
```
- Verify the `br-ex` interface, it should be like this
```bash
ip a s br-ex
6: br-ex: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UNKNOWN group default qlen 1000
    link/ether 0a:85:d1:87:0e:46 brd ff:ff:ff:ff:ff:ff
    # Added by kolla ansible
    inet 1.1.1.2/32 scope global br-ex
       valid_lft forever preferred_lft forever
    # Added by ovn-bgp agent, means that it can succesfully reach the interface
    inet 169.254.0.1/32 scope global br-ex
       valid_lft forever preferred_lft forever
    inet6 fd53:d91e:400:7f17::1/128 scope global
       valid_lft forever preferred_lft forever
    inet6 fe80::885:d1ff:fe87:e46/64 scope link
       valid_lft forever preferred_lft forever
```
- Do the same on the other network node. The output should be similar to above

```bash
ssh -F kolla-builder/ssh_config kolla-ovn-bgp-network-02
```
- If there's no `169.254.x.y` IP on either of the netwoek nodes, ssh to network and compute nodes to investigate logs  `/var/log/kolla/openvswitch/ovn-bgp-agent.log`
- SSH to deploy node again and try adding an openstack instance to demo-network
```bash
openstack server create --image cirros --network demo-net --flavor m1.tiny test
openstack server list
+-----------------------+------+--------+---------------------+--------+---------+
| ID                    | Name | Status | Networks            | Image  | Flavor  |
+-----------------------+------+--------+---------------------+--------+---------+
| 8d7806d6-4f7c-43d4-   | test | ACTIVE | demo-net=10.0.0.130 | cirros | m1.tiny |
| 8f5b-fd276770446b     |      |        |                     |        |         |
+-----------------------+------+--------+---------------------+--------+---------+
```
- SSH to one of the network nodes and see if the IP (e.g. `10.0.0.130` ) was added to `bgp-nic`
```bash
10: bgp-nic: <BROADCAST,NOARP,UP,LOWER_UP> mtu 1500 qdisc noqueue master bgp-vrf state UNKNOWN group default qlen 1000
    link/ether 16:23:48:49:bb:a6 brd ff:ff:ff:ff:ff:ff
    inet 192.168.100.193/32 scope global bgp-nic
       valid_lft forever preferred_lft forever
    inet 10.0.0.130/32 scope global bgp-nic
       valid_lft forever preferred_lft forever
    inet6 fe80::1423:48ff:fe49:bba6/64 scope link
       valid_lft forever preferred_lft forever
```
- If there's no IP then try the other network node
- Verify the IP is reachable via `ping` and also `ssh` - login as `cirros` user with password `gocubsgo`

### Spawn&Deploy Cloud 2
- In order for BGP to work, the clouds must share one network. We will use our SSH network for that, because then they can share the docker registry as well.
- Go to kolla-builder directory and add the following files
- `user/ovn-bgp-ngbr.yml`
```yaml

inventory_name: "ovn-bgp-multinode-neighbor"
image_pool: "/var/lib/libvirt/images"
image_path: "{{ image_pool }}/kolla-image.qcow2"
ara_enable: false
is_remote: true
remote_image_pool: "/var/lib/libvirt/images"
# SSH key for the remote host
proxy_server_private_key: "{{ lookup('ansible.builtin.env', 'HOME') }}/.ssh/id_rsa"


## NETWORK
# Use the Cloud 1 ssh network
network_ssh: "kolla-ssh-bgp"
# Use differnt networks for neutron and openstack
network_openstack: "kolla-openstack-bgp-nghbr"
network_neutron: "kolla-neutron-bgp-nghbr"

# Important, the IPs must not clash with Cloud 1, so use 100 as last digit
# Kolla builder spawns VMs with ssh ips in order
network_ssh_ip: "192.168.122.100"
# Differnet IPS
network_openstack_ip: "192.168.124.0"
network_neutron_ip: "192.168.125.0"

# Same virbr as cloud 1
network_ssh_bridge: virbr0
# Different virbrs
network_openstack_bridge: virbr4
network_neutron_bridge: virbr5

create_networks: true
destroy_networks: true

kolla_internal_vip_address: "192.168.124.200"
git_patch_kolla: true


git_branch: "ovn-bgp-agent"

git_patches: []
kolla_ssh_key: "{{ lookup('ansible.builtin.env', 'HOME') }}/.ssh/id_kolla"
globals_file: user-globals/ovn-bgp.yml
kolla_source_local_path: "../kolla-ansible"

# demo network should have differnt subnet than cloud1
demo_net_cidr: "10.10.10.0/24"
demo_net_gateway: "10.10.10.1"

is_aio: false

default_cpu: 12
default_ram: 1024
default_disksize: 25
nodes:
  - name: "kolla-ovn-bgp-ngbr-control-01"
    control: true 
    storage: true
    monitoring: true
    network: false
    compute: true
    ram_size: 8192

  - name: "kolla-ovn-bgp-ngbr-network-01"
    network: true
    ram_size: 4096

  - name: "kolla-ovn-bgp-ngbr-network-02"
    network: true
    ram_size: 4096

  - name: "kolla-ovn-bgp-ngbr-deployment"
    deployment: true
    ram_size: 1024
```
- Copy `kolla-files/user-globals/ovn-bgp-ngbr.yml` to `kolla-files/user-globals/ovn-bgp-ngbr.yml`
- Spawn and prepare the cloud

```bash
./builder -r spawn user/ovn-bgp-ngbr.yml && ./builder -r prepare user/ovn-bgp-ngbr.yml
```
- When spawned, SSH to the deployment node of the neighbor cloud and deploy Kolla
```bash
ssh -F kolla-builder/ssh_config kolla-ovn-bgp-ngbr-deployment
./deploy
```
- Perform simmilar checkups you did from cloud1 and spawn an instance on demo net.
### Connect the clouds (TODO test)
- In kolla builder directory edit `kolla-files/user-globals/ovn-bgp.yml` to match the following
```yaml
frr_neighbor_ips:
# IPs of the other cloud network nodes
- "192.168.122.102"
- "192.168.122.103"
```
- Same for  `kolla-files/user-globals/ovn-bgp-ngbr.yml`
```yaml
frr_neighbor_ips:
# IPs of the other cloud network nodes
- "192.168.122.5"
- "192.168.122.6"
```
- You can get the exact IPs of network nodes from `ssh_config` or `multinode` inventories on both clouds deploy nodes
- Update both clouds by running prepare playbooks
```bash
./builder -r prepare user/ovn-bgp.yml
./builder -r prepare user/ovn-bgp-ngbr.yml
```
- On both deployment nodes run
```bash
kolla-ansible -i multinode deploy --tags frr,ovn-bgp-agent
```
- On all 4 network nodes verify bgp connection and routing by running
```bash
docker exec frr vtysh -c "show bgp summary"
docker exec frr vtysh -c "show ip route"
```
- You should see all BGP routed IPs
- SSH to one of the cirros test instances and try `ping` and `ssh` with the other one and vice-versa

### Notes/TODO
- Only machines on clouds that directly share a network can be connected this way
- Tennant networks are exposed in all-or-nothing fashion if connected to the external router
- FIP exposing cannot be tested, because if the clouds share networks they are reachable without BGP anyway
