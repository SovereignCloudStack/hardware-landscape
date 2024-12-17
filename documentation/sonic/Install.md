## Base Installation

The following procedure describes to to reinstall an entire switch.

* Configure the DHCP Server
  * Set the image 
    * Configure ZTP and Image URL : `inventory/group_vars/network_switches/15_install.yml`
    * Activate installation mode: `inventory/host_vars/<node>/02_install.yml`
  * Config DHCP
    ```
    osism apply scs_dhcpd
    ```
* Restart device and select "Install SONiC" ONIE entry
  (Installs the entire switch from scratch)
* Perform base access configuration
  (DNS, SSH Key, admin password)
  ```
  ssh-keygen -f '/home/marc/.ssh/known_hosts' -R '<ip of host>'
  echo "YourPaSsWoRd" > /opt/configuration/secrets/conn_sonic
  osism apply scs_sonic_minimal -l st01-sw25g-r01-u40 --conn-pass-file  /opt/configuration/secrets/conn_sonic
  ```
* Perform base configuration
  * Login to switch
    ```
    ssh admin@<switch> 
    ```
  * Configure static ipv4
    ```
    config-setup factory
    HOSTN="$(hostname)"
    IP="$(ip --json  addr ls eth0|jq -r '.[0].addr_info[] | select(.family == "inet").local')"
    sudo config hostname $HOSTN
    sudo config interface ip add eth0 ${IP}/24 10.10.23.254
    show management_interface address
    ```
  * Disable uneeded services
    ```
    sudo config feature autorestart dhcp_relay disabled
    sudo config feature state dhcp_relay disabled
    sudo show feature config dhcp_relay
    sudo config ztp disable -y
    ```
  * Disable all interfaces except the uplink
    ```
    INTERFACES="$(show interfaces status|awk '$9 ~ "up" {print $1}'|grep -v "Ethernet0"|tr '\n' ',')"
    config interface shutdown $INTERFACES
    ```
  * Configure NTP
    ```
    config ntp add 10.10.23.254
    config ntp add 10.10.23.253
    ```
  * Configure Syslog server
    ```
    config syslog add 10.10.23.254
    ```

  * Configure SNNP server
    ```
    config snmp community replace public Eevaid7xoh4m
    config snmp community add lohz3kaG5ted RW
    #config snmp community del public
    show runningconfiguration snmp
    ```

  * Save configuration
    ```
    config save -y
    exec bash
    reboot
    ```
