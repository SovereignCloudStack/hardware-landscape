# Installation of the Manager Node


1. Create a Node Image for the manager Nodes
   ```commandline
    cat > /tmp/image.yaml <<EOF 
    asn_node_base: '42100210'
    interface1_asn: '65405'
    interface1_name: enp2s0f0np0
    interface2_asn: '65404'
    interface2_name: enp2s0f1np1
    ipv4_base: 10.10.21.
    ipv6_base: 'fd0c:cc24:75a0:1:10:10:21:'
    layer3_underlay: 'true'
    variant: '1'
    EOF
    ./create-image-flavor.sh -b node-image-build-1 -l
    ```
2. Deploy the operating system for both manager nodes
   * st01-mgmt-r01-u30
   * st01-mgmt-r01-u31
3. Ensure external access to manager node
   - Ensure that the port forwarding described in the [documentation of Networks](../System_Networks.md) is in place
   - Change the default password
     ```
     passwd osism
     ```
   - Establish external network access
     * Manually configure the external ip adress as described in the [documentation of Networks](../System_Networks.md)
     * Perform a connection check
       ```
       ping 8.8.8.8
       host scs.community
       ```
4. Install manager node [as described in the osism manual](https://osism.tech/de/docs/guides/deploy-guide/manager/)
