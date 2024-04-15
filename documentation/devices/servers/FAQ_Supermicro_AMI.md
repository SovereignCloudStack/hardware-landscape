# FAQ for Supermciro Servers with AMI BIOS

## Configure the Supermciro Servers

1. Install the tools
   ```
   cd setup
   ./00_install_sum.sh
   ```
2. Add the details about the server details in `Supermicro_<Model>.md`
3. Create the dhcp configuration and activate  the dhcp config
   ```
   cd setup
   ./01_establish_configs.sh
   ```
4. Let the servers follow the dhc configuration
5. Login to BMC and add the OOB linence to the system SFT-OOB-LIC
   (`Miscellaneous` -> `Activate Licence`)
6. Backup the initial config
   ```
   ./backup_config.sh <system> <system> ...
   git add -A config/*<system>*
   git commit -m "inital config" config/*<system>*
   ```
7. Configure the BMC
   (modifies the exported XML files)
   ```
   ./server_ctl --bmc_template <system> <system> ...
   ```
8. Upload configuration
   ```
   ./restore_config.sh <system>
   ./restore_config.sh <system>
   ./restore_config.sh ...
   ```
9. Repeat step 6


# Install System

```
./server_ctl --power_off <system> <system> ...
./server_ctl --install_os <system> ..<system>
```

# Clear product key

[SUM 2.4.0](https://www.supermicro.com/Bios/softfiles/11407/X11DPG-HGX2_3_3_HG11000V_SUM240.zip) provides a ClearProductKey command

```
./sum -i 10.10.23.11 -u ADMIN -p WALLA -c ClearProductKey --key_index 0
```
