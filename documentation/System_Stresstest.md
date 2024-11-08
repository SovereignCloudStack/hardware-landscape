# Deployment of the Hardware Landscape

### Create a larger amount of domains, projects and virtual machines

Test scenario:
  * 12 domains, with 5 projects each , with 12 machines each.
    * 9 domains
    * 45 projects
    * 540 virtual machines
  * 4GB RAM per machine, 2.1TB RAM in total
  * 10GB Disk per machine, 5.5TB DISK in total
* Remove the stresstestfile
  ```
  ssh scs-manager1
  mv /srv/www/stresstest.sh /srv/www/stresstest.sh.disabled
  ```
* Test the scenario
  ```
  ./landscape_ctl --config stresstest.yaml --create_domains stresstest1 --create_projects stresstest-project1 --create_machines stresstestvm1
  ```
* Execute the full szenario
  ```
  ./landscape_ctl --config stresstest.yaml --create_domains stresstest{1..9} --create_projects stresstest-project{1..5} --create_machines stresstestvm{1..12}
  openstack domain list
  openstack project list --long
  openstack server list --all-projects --long
  ```
* Activate the stresstestfile
  ```
  ssh scs-manager1
  cat <<EOF
  #!/bin/bash
  stress-ng --vm 8 --vm-bytes 80% -t 1h
  EOF
  mv /srv/www/stresstest.sh.disabled /srv/www/stresstest.sh
  ```
* Purge the scenario
  ```
  ./landscape_ctl --delete_domains stresstest{1..9}
  ```
