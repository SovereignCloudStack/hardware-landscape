# Performing configuration changes


1. Optional: Open a issue describing your goal and inform the users of the plattform
2. Check if there are active pull request for the environment
3. Perform the steps described by ["Working with GIT Branches"](https://osism.tech/docs/guides/configuration-guide/configuration-repository#working-with-git-branches)
   ```
   scs_switch_branch.sh <branchname>
   ```
4. Complete your technical work
5. Check if new documentation needs to be created
5. Handover the review to the maintainers of the system

# Upgrade BMC and BIOS of servers

1. Backup all configurations
   ```bash
   # identify the servers models for the filter
   ./server_ctl -s all -v
   SERVER_FILTER="device_model=H12SSL.*"
   ./server_ctl --backup_cfg both --filter "${SERVER_FILTER?SPECIFY FILTER}"
   git commit -s -m "backup configs before firmware update"  device_configurations/server/*
   ```
1. Download and extract the firmware, you find the references to the motherboards
   at [the documentation of the servers](./devices/servers/)
1. Store the the download file to the archive at the
   [private SCS repo](https://github.com/SCS-Private/orga-infra/tree/main/scs-system-landscape/firmware) location.
1. Open browser on the involved servers and upload firmware
   (This opens various tabs for the servers, you can cut & paste teh passwords to your browser session)
   ```
   ./server_ctl -o all --filter "${SERVER_FILTER?SPECIFY FILTER}"
   ```
1. Perform upgrades in a sequence
   * Upload BMC and perform upgrade
   * Upload BIOS (install BIOS on reboot)
   * Execute pre reboot steps
     * Control Nodes
     * Compute Nodes
       https://wiki.openstack.org/wiki/OpsGuide-Maintenance-Compute
     * Ceph Nodes
   * Open remote console and reboot server
     ```
     ssh <node> sudo halt
     # In theory this should start a shutdown of the server, but it seems that Supermicro just resets the hardware
     # without a graceful shutdown
     ./server_ctl --power_action GracefulRestart <node>
     ```
   * Test server after startup
   * Incubate the new version at least one day for the first server(s)
1. Backup all configurations and compare them if there are some unexpected changes
   ```
   ./server_ctl --backup_cfg both --filter "${SERVER_FILTER?SPECIFY FILTER}"
   git diff device_configurations/server/
   ```

