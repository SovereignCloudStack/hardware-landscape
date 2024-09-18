# Building a SONiC image

This guide provides step-by-step instructions to build a SONiC image, particularly focusing on optimizing build times.

## Prerequisites

### Hardware Requirements

- **CPU**: Minimum 8 cores (more cores for faster builds)
- **RAM**: Minimum 8 GB, recommended 32 GB
- **Storage**: At least 300 GB of free disk space
- **KVM Virtualization Support**: Required for build of VS (virtual switch) platform

### Software Requirements

- **Operating System**: Ubuntu 20.04 LTS is recommended
- **Python 3**: Install via package manager
- **Docker**: SONiC builds run in Docker containers

### Set Up Environment

- Install Required Packages
   ```bash
   sudo apt update
   sudo apt install -y python3-pip git
   pip3 install --user j2cli
   ```
- Install Docker
  Follow instructions [here](https://docs.docker.com/engine/install/ubuntu/) and install docker.
  You also need to add your user to the docker group as sudo is not supported:
  ```bash
  sudo usermod -aG docker ${USER}
  ```
  Log out and log back in to apply group changes.
- Ensure the 'overlay' module is loaded on your development system
  ```bash
  sudo modprobe overlay
  ```
- Clone the SONiC Repository
  ```bash
  git clone --recurse-submodules https://github.com/sonic-net/sonic-buildimage.git
  cd sonic-buildimage
  ```
- Ensure proper permissions for the build artifacts directory
  ```bash
  sudo mkdir -p /var/cache/sonic/artifacts
  sudo chown $USER: /var/cache/sonic/artifacts
  sudo chmod 777 /var/cache/sonic/artifacts
  ```

## Build image 

From the sonic-buildimage directory...

- Checkout a specific branch of sonic-buildimage. By default, the `master` branch is used, but you
  may want to build SONiC from some stable branch e.g. `202405` 
  ```bash
  git checkout master
  ```
- Initialize the Build Environment
  ```bash
  make init
  ```
- Execute make configure once to configure ASIC (this may take a while) see full list of supported vendors [here](https://github.com/sonic-net/sonic-buildimage?tab=readme-ov-file#usage)
  ```bash
  make configure PLATFORM=[ASIC_VENDOR]  # e.g. broadcom
  ```
- Build SONiC image (see the following options that helps you to optimize a build speed):
  - SONiC builds often download packages from multiple Debian distributions. To speed up builds, you can skip these
    unnecessary downloads, e.g. to avoid building Debian releases “jessie” and “stretch” use the following: `NOSTRETCH=1 NOJESSIE=1`
  - Increase the number of concurrent build jobs using the SONIC_BUILD_JOBS parameter to take full advantage of your
    system’s CPU cores. The SONiC build scripts take care of ensuring that dependencies are taken care in the right order
    when running parallel build jobs. Based on [this](https://support.stordis.com/hc/en-us/articles/19994539796381-How-to-build-the-community-version-of-SONiC-Virtual-Switch-SONiC-VS-image)
    docs there is no benefit to using more than 8 cores, so `SONIC_BUILD_JOBS=8` should be sufficient
  - By default, SONiC rebuilds all Docker images for every build, which can be time-consuming. To avoid recreating or 
    redownloading Docker images every time, SONiC offers a caching option. Enable the caching mechanism by setting the
    SONIC_DPKG_CACHE_METHOD environment variable to rwcache: `SONIC_DPKG_CACHE_METHOD=rwcache`
  - By default, SONiC uses the legacy Docker builder, but Docker BuildKit, introduced in Docker version 23, offers faster
    build times by skipping unused stages and parallelizing independent stages. Enable is via `SONIC_USE_BUILD_KIT=y`

  ```bash
  time NOSTRETCH=1 NOJESSIE=1 make SONIC_BUILD_JOBS=8 SONIC_DPKG_CACHE_METHOD=rwcache SONIC_USE_BUILD_KIT=y target/sonic-[ASIC_VENDOR].bin
  ```

## Known issues with build on branch `202405`

Refer to the following PRs and apply the patch below to the SONiC `202405` branch if these PRs have not yet been backported to the `202405` branch:
- https://github.com/sonic-net/sonic-buildimage/pull/20241
- https://github.com/sonic-net/sonic-buildimage/pull/18789

```text
diff --git a/rules/ipmitool.mk b/rules/ipmitool.mk
index aad6fea3a..a3d084524 100644
--- a/rules/ipmitool.mk
+++ b/rules/ipmitool.mk
@@ -1,6 +1,6 @@
 # ipmitool packages
 IPMITOOL_VERSION = 1.8.19
-IPMITOOL_VERSION_SUFFIX = 4
+IPMITOOL_VERSION_SUFFIX = 4+deb12u1
 IPMITOOL_VERSION_FULL = $(IPMITOOL_VERSION)-$(IPMITOOL_VERSION_SUFFIX)
 IPMITOOL = ipmitool_$(IPMITOOL_VERSION_FULL)_$(CONFIGURED_ARCH).deb
 $(IPMITOOL)_SRC_PATH = $(SRC_PATH)/ipmitool
diff --git a/src/sonic-build-hooks/scripts/buildinfo_base.sh b/src/sonic-build-hooks/scripts/buildinfo_base.sh
index 9adcb1d3b..1f4d0973b 100755
--- a/src/sonic-build-hooks/scripts/buildinfo_base.sh
+++ b/src/sonic-build-hooks/scripts/buildinfo_base.sh
@@ -124,10 +124,10 @@ set_reproducible_mirrors()
         expression3="/#SET_REPR_MIRRORS/d"
     fi
     if [[ "$1" != "-d" ]] && [ -f /etc/apt/sources.list.d/debian.sources ]; then
-        mv /etc/apt/sources.list.d/debian.sources /etc/apt/sources.list.d/debian.sources.back
+        $SUDO mv /etc/apt/sources.list.d/debian.sources /etc/apt/sources.list.d/debian.sources.back
     fi
     if [[ "$1" == "-d" ]] && [ -f /etc/apt/sources.list.d/debian.sources.back ]; then
-        mv /etc/apt/sources.list.d/debian.sources.back /etc/apt/sources.list.d/debian.sources
+        $SUDO mv /etc/apt/sources.list.d/debian.sources.back /etc/apt/sources.list.d/debian.sources
     fi
 
     local mirrors="/etc/apt/sources.list $(find /etc/apt/sources.list.d/ -type f)"
```

---
References:
- [Capgemini: Faster SONiC Builds for Effective CI/CD Processes](https://www.capgemini.com/insights/expert-perspectives/faster-sonic-builds-for-effective-ci-cd-processes/)
- [STORDIS: How to Build the Community Version of SONiC Virtual Switch](https://support.stordis.com/hc/en-us/articles/19994539796381-How-to-build-the-community-version-of-SONiC-Virtual-Switch-SONiC-VS-image)
- [SCS Community: SONiC Build Optimization](https://input.scs.community/sonic-built-optimization#)
