# SONiC development

To develop on SONiC NOS efficiently, here are the key steps and techniques compiled from various sources.

The SONiC packages often depend on several other packages, some available on PyPI and others within the SONiC codebase.
To properly build or test SONiC packages, you must install these dependencies manually or let the SONiC build system
handle the setup. SONiC build system configures a complete environment with all dependencies inside a Docker container.

## Prerequisites

Follow and apply instructions [here](Build.md#prerequisites).

## Development

From the sonic-buildimage directory...

- Checkout a specific branch of `sonic-buildimage` repository. By default, the `master` branch is used, it may be a good idea to
  develop against this branch. Ensure `master` branch:
  ```bash
  git checkout master
  ```
- Initialize the build environment
  ```bash
  make init
  ```
- Execute make configure once to configure ASIC (this may take a while). See full list of supported vendors [here](https://github.com/sonic-net/sonic-buildimage?tab=readme-ov-file#usage).
  You can use `vm` if you want to test your feature/fix in the virtual switch environment, or you can also use `generic`
  platform as a placeholder:
  ```bash
  make configure PLATFORM=vm
  ```
- List build targets to get a list of available `.deb` (debian package) and `.whl` (python wheel) targets
  for different SONiC components, like `sonic_frr_mgmt_framework` or other platform-specific targets.
  ```bash
  $make list
  ...
  target/debs/bookworm/sonic-platform-vs_1.0_amd64.deb
  target/debs/bookworm/sonic-dhcp6relay-dbgsym_1.0.0-0_amd64.deb
  target/debs/bookworm/sonic-eventd-dbgsym_1.0.0-0_amd64.deb
  target/debs/bookworm/sonic-rsyslog-plugin_1.0.0-0_amd64.deb
  target/debs/bookworm/iccpd-dbg_0.0.5_amd64.deb
  target/debs/bookworm/ipmitool-dbgsym_1.8.19-4+deb12u1_amd64.deb
  ...
  target/python-wheels/bookworm/sonic_containercfgd-1.0-py3-none-any.whl
  target/python-wheels/bookworm/sonic_ctrmgrd-1.0.0-py3-none-any.whl
  target/python-wheels/bookworm/sonic_dhcp_utilities-1.0-py3-none-any.whl
  target/python-wheels/bookworm/sonic_frr_mgmt_framework-1.0-py3-none-any.whl
  target/python-wheels/bookworm/sonic_utilities-1.2-py3-none-any.whl
  ...
  ```

- Build the target package, e.g. `sonic_frr_mgmt_framework` python wheel package, within the debian bookworm slave container.
  Instruct the system to keep the container running after the build completes:
  ```bash
  make -f Makefile.work BLDENV=bookworm KEEP_SLAVE_ON=yes target/python-wheels/bookworm/sonic_frr_mgmt_framework-1.0-py3-none-any.whl
  ```
  - If the make command immediately finishes with the message "Nothing to do, the package is up-to-date", it indicates
    that the package has already been built during a previous image build and is up to date. In this case, simply remove
    the package and proceed:
    ```bash
    rm target/python-wheels/bookworm/sonic_frr_mgmt_framework-1.0-py3-none-any.whl
    ```
- When the build finishes, your prompt will change to indicate you are inside the slave container. Change into the package directory:
  ```bash
  user@58b655f15722:/sonic$ cd src/sonic-utilities/
  ```
- Now that you are in the development environment, you can start editing the package source code, build it, or run its unit
  tests. 
  - You can edit files on your local, as your local `sonic-buildimage` clone is mounted to `/sonic` directory in the
    slave container. Validate slave container mounts as follows (from your local): 
    ```bash
    $ docker ps | grep sonic
    58b655f15722   sonic-slave-bookworm-user:c243baccce2   "bash -c 'make -f sl…"   7 minutes ago   Up 7 minutes       22/tcp    peaceful_darwin
    $ docker inspect -f '{{ .Mounts }}' 58b655f15722
    ```
  - Most unit tests in SONiC use the pytest framework. To run tests, use
  ```bash
  python3 setup.py test
  ```  
  - To build the python package after making changes (to specify the destination for the built package, use the -d option):
  ```bash
  python3 setup.py bdist_wheel # -d /desired/output/location
  ```

## Deploying the developed package on a SONiC device

Obviously, when developing, it is quite inefficient to build the whole SONiC image each time and then do a full installation of it.
We can choose not to install the image and use the direct upgrade of newly developed package to do a partial upgrade,
thus improving our development efficiency.
To do this, upload the new package to the `/etc/sonic` directory of the switch, which will automatically map to the 
`/etc/sonic` directory inside all containers. Then, enter the relevant container and use the suitable command to install
the package:

```bash
# Enter the docker container inside SONiC switch
docker exec -it <container> bash
# Install the package
# For .deb package:
dpkg -i <deb-package>
# For python package (note: Don't use "--force-reinstall"): 
sudo pip uninstall YOUR_WHEEL_PACKAGE
sudo pip install YOUR_WHEEL_PACKAGE 
```
