# General Information

* Documentation Overview: https://sonicfoundation.dev/resources-for-users/
* SONiC Command Line Interface Guide: https://github.com/sonic-net/sonic-utilities/blob/master/doc/Command-Reference.md
* Onie Commandline: https://opencomputeproject.github.io/onie/cli/index.html
* Community Interaction
  * Dev Chat on https://lists.sonicfoundation.dev/g/sonic-dev
  * Redit on https://www.reddit.com/r/sonicnos/
  * Matrix on https://matrix.to/#/#sonic-net:matrix.org
  * Linkedin on https://www.linkedin.com/groups/12633489/
  * "Good lab environment and very active Discord community" on https://containerlab.dev/manual/kinds/


# Playing / Testing

* Sonic Software Switch
  https://github.com/sonic-net/SONiC/wiki/SONiC-P4-Software-Switch seems to to be a valid functionality anymore
  (https://github.com/sonic-net/SONiC/issues/1618)

* A virtual machine : https://sonic.software/
  ```
  DIR="$(mktemp -d /tmp/sonic.XXXXX)
  cd $DIR
  wget https://sonic.software/download-gns3a.sh
  chmod +x download-gns3a.sh
  ./download-gns3a.sh master

  qemu-system-x86_64 -machine q35 -m 4096 -smp 4 -hda sonic*.img \
    -monitor telnet::45454,server,nowait \
    -nographic -netdev user,id=sonic0,hostfwd=tcp::5555-:22 \
    -device e1000,netdev=sonic0 -cpu host -accel kvm

  # Password admin / YourPaSsWoRd
  ssh admin@localhost -p 5555

  # Control QEMU:
  telnet localhost 45454

  # Stop it the hard way
  killall qemu-system-x86_64
  ```
* GNS3 Simulation environment: https://gns3.com/ (untested)

# FAQ for Edgecore Switches

## Serial Switch Console Access

* Attach to a running screen session which provides access to the ttypS0..ttyS3 interfaces
  or create automatically a new one
  ```
  scs_serial_access
  ```
  -> Leave with "STRG+y d" (we use a different command/escape key)
* Restart all sessions
  1. Attach to running session
     ```
     scs_serial_access
     ```
  2. Terminate sessions by STRG+y :quit
  3. Restart terminals
     ```
     scs_serial_access
     ```
* Review console output
  see /var/log/screen


## Use Sysrq to restart

https://www.kernel.org/doc/html/latest/admin-guide/sysrq.html

- Open a serial sccreen to the hardware
- Use the screen command (STRG+y or STRG+a) to send a break signal
  :break<ENTER>
- Hit the sysrq char "b" multiple times
- Watch the hardware booting :-)

## Sonic: Show Serial number of hardware

* SONiC
  ```
  show version|less
  show platform syseeprom # in the case when the previous command does not show the serial
  ```
* ONIE
  ```
  onie-sysinfo -s # Serial
  onie-sysinfo -m -s -e
  463054TE2315074 d0:77:ce:2b:31:c4 accton_as4630_54te
  ```

## ONIE: Install SONIC

- Enter the ONIE install OS mode
Note: Switch will automatically enter the ONIE install mode if there’s no NOS installed.
```
                          GNU GRUB  version 2.02
 +----------------------------------------------------------------------------+
 |*ONIE: Install OS    <----- Select this one                                 |
 | ONIE: Rescue                                                               |
 | ONIE: Uninstall OS                                                         |
 | ONIE: Update ONIE                                                          |
 | ONIE: Embed ONIE                                                           |
 +----------------------------------------------------------------------------+

      Use the ^ and v keys to select which entry is highlighted.
      Press enter to boot the selected OS, `e' to edit the commands
      before booting or `c' for a command-line.
```

- Stop ONIE Service Discovery :
```
ONIE:/ # onie-stop
discover: installer mode detected.
Stopping: discover... done.
```

- Install the image from the remote URL

We assume you have uploaded SONiC image onto a http server (192.168.0.4).

```
ONIE:/ # onie-nos-install http://10.10.23.1/sonic-fix_scs-459.0-dirty-20231215.160917.bin
```
When NOS installation finishes, the box will reboot into SONiC by default.
```
```
## ONIE: Uninstall SONIC

- Reboot the switch:
```
admin@sonic:~$ sudo reboot
```

- While booting from ONIE enter "Uninstall OS"

```
                          GNU GRUB  version 2.02
 +----------------------------------------------------------------------------+
 |*ONIE: Install OS                                                           |
 | ONIE: Rescue                                                               |
 | ONIE: Uninstall OS  <----- Select this one                                 |
 | ONIE: Update ONIE                                                          |
 | ONIE: Embed ONIE                                                           |
 +----------------------------------------------------------------------------+

      Use the ^ and v keys to select which entry is highlighted.
      Press enter to boot the selected OS, `e' to edit the commands
      before booting or `c' for a command-line.
```

ONIE will completely uninstall SONIC OS including erasing the disk storage and the device will be clean from any installed NOS.
```
```
## SONiC Install and Remove images

- Check the images:
  ```
  # sonic-installer list
  ```
- Install an image from remote HTTP server:
  ```
  # sonic-installer install http://192.168.0.4/sonic-master.bin
  ```
- Reboot device:
  ```
  $ sudo reboot
  ```
- Specify the default image:
  Check the images:
  ```
  # sonic-installer list
  Current: SONiC-OS-master-nb-inno.0-2d2d4bce
  Next: SONiC-OS-master-nb-inno.0-2d2d4bce
  Available:
  SONiC-OS-master-nb-inno.0-2d2d4bce
  SONiC-OS-202012-nb-inno.0-25af05a8
  ```

  ``
- Set the default boot-up image:
  ```
  # sonic-installer set-default SONiC-OS-202012-nb-inno.0-25af05a8
  ```

- Check the image status:
  ```
  # sonic-installer list
  Current: SONiC-OS-master-nb-inno.0-2d2d4bce
  Next: SONiC-OS-202012-nb-inno.0-25af05a8
  Available:
  SONiC-OS-master-nb-inno.0-2d2d4bce
  SONiC-OS-202012-nb-inno.0-25af05a8
  ```

- Remove and check the images:
  ```
  # sonic-installer list
  Current: SONiC-OS-202012-nb-inno.0-25af05a8
  Next: SONiC-OS-202012-nb-inno.0-25af05a8
  Available:
  SONiC-OS-master-nb-inno.0-2d2d4bce
  SONiC-OS-202012-nb-inno.0-25af05a8

  # sonic-installer remove SONiC-OS-master-nb-inno.0-2d2d4bce

  # sonic-installer list
  Current: SONiC-OS-202012-nb-inno.0-25af05a8
  Next: SONiC-OS-202012-nb-inno.0-25af05a8
  Available:
  SONiC-OS-202012-nb-inno.0-25af05a8
  ```

   Note: \
       “Current” image, it mean the running image \
       “Next” image, it mean the next boot up image \
       “Available” images, it mean installed SONiC images



## Install a release from a running system

```
sonic-installer install http://10.10.23.1/~ignatov17/Edgecore-SONiC_20230420_055428_ec202111_370.bin
sonic-installer list
sonic-installer set-default SONiC-OS-Edgecore-SONiC_20230420_055428_ec202111_370
```


## Update a switch to the SONiC image


1. Create a backup of the current config
   ```
   SWITCH="st01-sw25g-r01-u34"
   ./backup_switches.sh $SWITCH
   git diff config/*${SWITCH}*json
   ```
2. Shutdown all ports on the environmental switches
   ```
   ssh <environmental switch>
   lldpshow
   config interface shutdown EthernetX,EthernetX,...
   ```
3. Restart the device and select "ONIE" in the grub prompt and "Install OS"
4. Start the installation
   ```
   ssh scs-jumphost
   ssh $SWITCH
   scs_serial_access
     -> STRG+y, :break + b
   onie-nos-install http://10.10.23.1/sonic-fix_scs-459.0-dirty-20231215.160917.bin
   ```
5. Boot the system
6. Reestablish the configuration
   ```
   cd setup
   ./01_distribute_keys.sh $SWITCH
   ./02_setup_os.sh $SWITCH
   cd ..
   ./restore_switches.sh $SWITCH # Reboot
   ```
7. Startup the ports on the environmental switches
   ```
   ssh <environmental switch>
   sudo config interface shutdown EthernetX,EthernetX,...
   ```
8. Rexecute a backup to check if the righ config is established i
   (no differences should appear)
   ```
   ./backup_switches.sh $SWITCH
   ```

## Access Package Repositories

* Set a proxy
  ```
  export http_proxy="http://10.10.23.1:8888"
  export https_proxy="http://10.10.23.1:8888"
  ```
* Install extra software
  ```
  apt-get update && apt-get upgrade
  apt-get install git
  ```
* Use package manager: https://github.com/sonic-net/sonic-utilities/blob/master/doc/Command-Reference.md#sonic-package-manager
* Add additional Domains
  ```
  ssh scs-jumphost
  /etc/tinyproxy/filter-allow
  systemctl restart tinyproxy
  ```

## Disable all ports


* Show all connected interfaces
  ```
  show interfaces status|awk '/"Oper Speed/{print $0} $9 ~ "up" && $8 == "up" {print $0;count++}END{print "\n" count " links"}'
  lldpshow
  ```

* Disable all interfaces
  ```
  INTERFACES="$(show interfaces status|awk '$9 ~ "up" {print $1}'|tr '\n' ',')"
  sudo config interface shutdown $INTERFACES
  ```

* Enable all interfaces
  ```
  INTERFACES="$(show interfaces status|awk '$9 ~ "down" {print $1}'|tr '\n' ',')"
  sudo config interface startup $INTERFACES
  ```

* Disable all Ports which do not have a link
  ```
  INTERFACES="$(show interfaces status|awk '$9 ~ "up" && $8 == "down" {print $1}'|tr '\n' ',')"
  sudo config interface shutdown $INTERFACES
  ```

## VLANs

```
config vlan add 23
config vlan member add -u 23 Interface0
config vlan member add -u 24 Interface0
config vlan member add -u 25 Interface0
config vlan member add 23 Interface0
config vlan member add 24 Interface0
config vlan member add 24 Interface0
show vlan brief

show interfaces status|awk '$8 == "up" && $7 x== "routed" {printf("config vlan member del 23 %s\n",$1)}' 
show vlan brief
```

## Portchannel

```
config portchannel add PortChannel01
config vlan member del 25 Ethernet120
config vlan member del 25 Ethernet124
config vlan member del 26 Ethernet124
config vlan member del 26 Ethernet120
config portchannel member add PortChannel01 Ethernet120
config portchannel member add PortChannel01 Ethernet124
config vlan member add 25 PortChannel01
config vlan member add 26 PortChannel01
show interfaces status PortChannel01
```


## Factory config

```
rm /etc/sonic/config_db.json
config-setup factory
reboot
```

## Managment VRF

https://github.com/sonic-net/SONiC/blob/master/doc/mgmt/sonic_stretch_management_vrf_design.md#terminating-on-the-switch


## Interact with redis

```
sonic-db-cli CONFIG_DB HSET 'DEVICE_METADATA|localhost' mac 02:77:ce:2b:3f:c4
sonic-db-cli CONFIG_DB HGET 'DEVICE_METADATA|localhost'
```


## Setup the managment IP on a VLAN Interface

* Setup: "Prevent duplicate MAC adresses"
  ```
  vi /etc/sonic/config_db.json
  config load
  reboot
  ```
* Configure on VLAN
  ```
  sudo bash
  HOSTN="$(hostname)"
  IP="$(ip --json  addr ls eth0|jq -r '.[0].addr_info[] | select(.family == "inet").local')"

  config interface ip remove eth0 ${IP}
  ip addr ls eth0
  show management_interface address # no result


  config vlan add 23
  #config interface ip add Vlan23 ${IP}/24 10.10.23.1
  config interface ip add Vlan23 ${IP}/24 
  ip addr ls Vlan23
  config route add prefix 0.0.0.0/0 nexthop 10.10.23.1
  show ip route |grep 0.0.0.0/0

  config save -y
  ```

## Base configuration

```
config-setup factory
```

```
ssh <switch> # YourPaSsWoRd

sudo bash
HOSTN="$(hostname)"
IP="$(ip --json  addr ls eth0|jq -r '.[0].addr_info[] | select(.family == "inet").local')"

cat > /etc/resolv.conf << 'EOF'
nameserver 8.8.8.8
nameserver 9.9.9.9

search mgmt.sovereignit.de
EOF


config interface ip add eth0 ${IP}/24 10.10.23.1
show management_interface address

sudo config feature autorestart dhcp_relay disabled
config feature state dhcp_relay disabled
sudo show feature config dhcp_relay

INTERFACES="$(show interfaces status|awk '$9 ~ "up" {print $1}'|grep -v "Ethernet0"|tr '\n' ',')"
config interface shutdown $INTERFACES

config interface ip add eth0 ${IP}/24 10.10.23.1

config hostname $HOSTN

config ntp add 192.53.103.103
config ntp add 192.53.103.104
config ntp add 192.53.103.108

config syslog add 10.10.23.1

config snmp community replace public Eevaid7xoh4m
config snmp community add lohz3kaG5ted RW
#config snmp community del public
show runningconfiguration snmp


config ztp disable -y
config save -y
exec bash
reboot


show management_interface address
sudo mii-tool eth0
ping -c 3 10.10.23.1

```


## Static Routes

Unreliable, SONiC forgets that after a few minutes.
```
config route add prefix 0.0.0.0/0 nexthop 10.10.23.1
```

## Backup switch configuration

```
./backup_switches.sh # all switches
./backup_switches.sh st01-sw1g-r01-u42
git status
git diff
git add
git commit
```

## Restore switch configuration

```
./restore_switches.sh # all switches
./restore_switches.sh st01-sw1g-r01-u42
```

* Before perfoming a restore the scripts takes a backup fo the current configuration
* The previous configuration is backuped at `config_db_backup_${timestamp}.json`

## Prevent duplicate MAC adresses

A fresh sonic system assigns the mac addresses of the management interface also to all front interfaces.

```
# ip -json link ls | jq -r '.[] | "\(.ifname) \(.address)"'
lo 00:00:00:00:00:00
eth0 90:2d:77:58:26:50
eth1 90:2d:77:58:26:51
eth2 90:2d:77:58:26:52
bcm0 02:10:18:41:a9:50
docker0 02:42:50:f5:1e:e7
Ethernet0 90:2d:77:58:26:50
Ethernet4 90:2d:77:58:26:50
...
```

This can be a problem when the switch is connected by managment port and by i.e. Ethernet0 to
the same vlans/networks. This means that the same MAC address appears on on different ports of your
switch infrastructure. Packets appear then alternately or randomly to the port on which the IP address is configured or
to the port on which the IP address is not configured.
That results in very unstable connections.

You can fix that by defining a dedicated mac address for the EthernetX ports.

Change the mac adress to a adress which is in one of the [private MAC address ranges](https://en.wikipedia.org/wiki/MAC_address#Ranges_of_group_and_locally_administered_addresses).
```
diff --git a/hardware/network/config/Edgecore_4630-54TE-O-AC-B_st01-sw1g-r01-u32.json b/hardware/network/config/Edgecore_4630-54TE-O-AC-B_st01-sw1g-r01-u32.json
index 2e5455a..0071378 100644
--- a/hardware/network/config/Edgecore_4630-54TE-O-AC-B_st01-sw1g-r01-u32.json
+++ b/hardware/network/config/Edgecore_4630-54TE-O-AC-B_st01-sw1g-r01-u32.json
@@ -311,21 +311,21 @@
   },
   "DEVICE_METADATA": {
     "localhost": {
       "buffer_model": "traditional",
       "default_bgp_status": "up",
       "default_pfcwd_status": "disable",
       "docker_routing_config_mode": "split",
       "frr_mgmt_framework_config": "true",
       "hostname": "st01-sw1g-r01-u32",
       "hwsku": "Accton-AS4630-54TE",
-      "mac": "d0:77:ce:2b:3f:c4",
+      "mac": "02:77:ce:2b:3f:c4",
       "platform": "x86_64-accton_as4630_54te-r0",
       "synchronous_mode": "enable",
       "type": "LeafRouter"
     }
   },
   "FEATURE": {
```

Simple:
```
sed -i '~s,d0:77,d2:77,g;~s,90:2d,92:2d,g' *.json
sonic-db-cli CONFIG_DB HSET 'DEVICE_METADATA|localhost' mac $(sonic-db-cli CONFIG_DB HGET 'DEVICE_METADATA|localhost' mac |sed '~s,^\(.\).,\12,')
```

Restart the switch, and check the settings:
```
lo 00:00:00:00:00:00
docker0 02:42:2d:27:64:56
eth3 d0:77:ce:2b:3f:c5
eth1 d0:77:ce:2b:3f:c6
eth0 d0:77:ce:2b:3f:c4 <- still the same
bcm0 02:10:18:09:10:15
Bridge 02:77:ce:2b:3f:c4
dummy 3a:1f:2d:41:ff:0f
Vlan23 02:77:ce:2b:3f:c4
Ethernet25 02:77:ce:2b:3f:c4 <- changed
Ethernet24 02:77:ce:2b:3f:c4
```

The setting does not change the Mac address to eth0, but to EthernetX or the bridge interface.


# Remove ip adresses from interfaces

Outputs the suitable commands
```
ip -json addr ls | jq -r '.[] | select(.ifname | startswith("Ethernet")) | "config interface ip remove \(.ifname) \(.addr_info[].local)"'
```

