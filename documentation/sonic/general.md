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
  * A page, with guides and tutorials https://www.sonicnos.net

# Playing / Testing

## Sonic Software images

There are two reliable places to find SoNiC software images:
* The output of the automated build pipeline that run in the [sonic-buildimage](https://github.com/sonic-net/sonic-buildimage) repository.
  * The artifacts are located at https://sonic-build.azurewebsites.net/ui/sonic/Pipelines
* An unofficial automatic index of the latest SONiC installation images: https://sonic.software/

Find additional information about image sources and procedure on how to find the SONiC image in the Azure pipeline artifacts [here](https://containerlab.dev/manual/kinds/sonic-vm/#getting-sonic-images).

## Sonic Software Switch (depreciated)

SoNiC wiki describes using the [SoNiC P4 Software switch](https://github.com/sonic-net/SONiC/wiki/SONiC-P4-Software-Switch),
don't bother to try, this functionality has been depreciated but the Docs still exist, see also [#1618](https://github.com/sonic-net/SONiC/issues/1618). 

## A virtual machine

Download a SONiC VS KVM image, e.g. from https://sonic.software/
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

Note: Find an extended tutorial of building a VM virtual lab using the SONiC VS KVM image [here](https://www.sonicnos.net/content/tutorials/virtual_lab)

## A docker container

Download a SONiC VS docker image, e.g. from https://sonic.software/
Find the tutorials [here](https://github.com/sonic-net/sonic-buildimage/blob/master/platform/vs/README.vsdocker.md) or [here](https://github.com/sonic-net/sonic-swss/blob/master/tests/README.md#setting-up-a-persistent-testbed)
to build lightweight testbed environment of SONiC using docker (not tested).

## GNS3 Simulation environment

This section guides you to create and import a SONiC appliance into [GNS3](https://www.gns3.com/).
Tutorial took inspiration from the following [blog post](https://pine-networks.com/blog/setting-up-sonic-on-gns3/) (note that the blog post is
outdated and refers to the depreciated SoNiC P4 Software switch image).

* Install and launch GNS3
  * Select the installer for your favourite OS: https://www.gns3.com/software/download
* Download a VS SONiC image, refer to [Sonic Software images](#sonic-software-images)
  * A convenient way how to download and extract the image and also create GNS3 appliance file is via the 
    download script available at https://sonic.software/download-gns3a.sh
    ```bash
    wget https://sonic.software/download-gns3a.sh
    chmod +x download-gns3a.sh
    ./download-gns3a.sh <release number>  # 202311
    ```
  * The above will download the latest image for the giver release number and create a GNS3 appliance file named e.g. `SONiC-202012-27914.gns3a`
    * Note that the 202405 release of SONiC VS image is not working due to [#19399](https://github.com/sonic-net/sonic-buildimage/issues/19399)
    * The release 202311 has also some bugs, like [#13317](https://github.com/sonic-net/sonic-buildimage/issues/13317) but works "better" then 202405 (if you can live without sonic-cli)
* From this point you can follow the instructions provided in https://pine-networks.com/blog/setting-up-sonic-on-gns3/.
  * Skip the initial instructions and start with the importing of appliance file you generated above e.g. `SONiC-202012-27914.gns3a`
  * Once you import the SONiC image you can create a new project or open the existing one and start using the SONiC
    appliance in GNS3 by dragging the SONiC appliance into the main window of your GNS3 project
