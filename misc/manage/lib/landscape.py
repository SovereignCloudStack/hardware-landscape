import logging
import re
import sys
from pprint import pformat

from openstack.exceptions import ResourceNotFound, SDKException
from openstack.connection import Connection
from openstack.compute.v2.keypair import Keypair
from openstack.compute.v2.server import Server
from openstack.identity.v3.domain import Domain
from openstack.identity.v3.project import Project
from openstack.identity.v3.user import User
from openstack.network.v2.network import Network
from openstack.network.v2.router import Router
from openstack.network.v2.security_group import SecurityGroup
from openstack.network.v2.subnet import Subnet

KEYPAIR_NAME = "my_ssh_public_key"
LOGGER = logging.getLogger()

CONFIG: dict[str,str|dict[str, str]] = dict()

def get_config(key: str, regex: str = ".+",
               multi_line: bool = False, parent_key: str = None, default: str | list[str] = None ) -> str | list[str]:
    lines = default
    try:
        if parent_key:
            lines = str(CONFIG[parent_key][key]).splitlines()
        else:
            lines = str(CONFIG[key]).splitlines()
    except KeyError as e:
        LOGGER.info(f"config does not contain : {parent_key} -> {key} : {pformat(CONFIG)}")
        if lines is None:
            sys.exit(1)


    if len(lines) > 1 and multi_line is False:
        LOGGER.error(f"{key}='{CONFIG[key]}' contains multiple lines")
        sys.exit(1)

    for line in lines:
        if not re.fullmatch(regex, str(line)):
            LOGGER.error(f"{key}='{CONFIG[key]}' does not match to regex >>>{regex}<<<")
            sys.exit(1)

    if not multi_line:
        return str(lines[0])
    else:
        return [str(val) for val in lines]

class SCSLandscapeTestUser:

    def __init__(self, conn: Connection, user_name: str, domain: Domain):
        self.conn = conn
        self.user_name = user_name
        self.user_password = get_config("admin_domain_password")
        self.domain: Domain = domain
        self.obj = self.conn.identity.find_user(user_name, query={"domain_id": self.domain.id})

    def assign_role_to_user(self, role_name: str):
        self.conn.identity.assign_project_role_to_user(self.obj.id, self.domain.id, self.get_role_id_by_name(role_name))
        LOGGER.info(f"Assigned role '{role_name}' to user '{self.obj.name}' in domain '{self.domain.name}'")

    def create_and_get_user(self) -> User:

        if self.obj:
            LOGGER.info(f"User {self.user_name} already exists in {self.domain.name}")
            return self.obj

        self.obj = self.conn.identity.create_user(
            name=self.user_name,
            password=self.user_password,
            domain_id=self.domain.id,
            enabled=True
        )
        self.assign_role_to_user("manager")
        LOGGER.info(
            f"Created user {self.obj.name} / {self.obj.id} with password {self.obj.password} in {self.domain.name}")
        return self.obj

    def delete_user(self):
        if not self.obj:
            return
        self.conn.identity.delete_user(self.obj.id)
        LOGGER.warning(f"Deleted user: {self.obj.name} / {self.obj.id}")
        self.obj = None

    def get_role_id_by_name(self, role_name) -> str:
        for role in self.conn.identity.roles():
            if role.name == role_name:
                return role.id
        raise RuntimeError(f"No such role {role_name}")


class SCSLandscapeTestNetwork:

    def __init__(self, conn: Connection, project: Project,
                 security_group_name_ingress: str, security_group_name_egress: str):
        self.project: Project = project
        self.conn = conn
        self.network_name = f"localnet-{self.project.name}"
        self.subnet_name = f"localsubnet-{self.project.name}"
        self.router_name = f"localrouter-{self.project.name}"
        self.security_group_name_ingress = security_group_name_ingress
        self.security_group_name_egress = security_group_name_egress
        self.obj_network: Network | None = SCSLandscapeTestNetwork._find_network(self.network_name, conn, project)
        self.obj_subnet: Subnet | None = SCSLandscapeTestNetwork._find_subnet(self.network_name, conn, project)
        self.obj_router: Router | None = SCSLandscapeTestNetwork._find_router(self.router_name, conn, project)
        self.obj_ingress_security_group: SecurityGroup | None = SCSLandscapeTestNetwork._find_security_group(
            self.security_group_name_ingress, conn, project)
        self.obj_egress_security_group: SecurityGroup | None = SCSLandscapeTestNetwork._find_security_group(
            self.security_group_name_egress, conn, project)

    @staticmethod
    def _find_security_group(name, conn: Connection, project: Project) -> SecurityGroup | None:
        security_groups = [group for group in conn.network.security_groups(name=name, project_id=project.id, domain_id=project.domain_id)]
        if len(security_groups) > 1:
            raise RuntimeError(f"Error fetching security group for project {project.name}/{project.domain_id} - {e}")
        elif len(security_groups) == 1:
            return security_groups[0]
        return None

    @staticmethod
    def _find_router(name, conn: Connection, project: Project) -> Network | None:
        routers = [router for router in conn.network.routers(name=name, project_id=project.id)]
        if len(routers) == 0:
            return None
        elif len(routers) == 1:
            return routers[0]
        else:
            raise RuntimeError(f"More than one router with the name {name} in {project.name}")

    @staticmethod
    def _find_network(name, conn: Connection, project: Project) -> Network | None:
        networks = [network for network in conn.network.networks(name=name, project_id=project.id)]
        if len(networks) == 0:
            return None
        elif len(networks) == 1:
            return networks[0]
        else:
            raise RuntimeError(f"More the one network with the name {name} in {project.name}")

    @staticmethod
    def _find_subnet(name, conn, project) -> Network | None:
        subnet = [network for network in conn.network.subnets(name=name, project_id=project.id)]
        if len(subnet) == 0:
            return None
        elif len(subnet) == 1:
            return subnet[0]
        else:
            raise RuntimeError(f"More the one subnet with the name {name} in {project.name}")

    def create_and_get_network_setup(self) -> Network:
        network = self.create_and_get_network()
        subnet = self.create_and_get_subnet()
        self.create_and_get_router(subnet)
        self.create_and_get_ingress_security_group()
        self.create_and_get_egress_security_group()

        return network

    def create_and_get_router(self, subnet: Subnet) -> Router | None:
        public_network = self.conn.network.find_network('public')
        if not public_network:
            LOGGER.error("There is no 'public' network")
            return None

        if self.obj_router:
            return self.obj_router

        self.obj_router = self.conn.network.create_router(
            name=self.router_name,
            admin_state_up=True
        )
        LOGGER.info(f"Router '{self.obj_router.name}' created with ID: {self.obj_router.id}")
        self.conn.network.update_router(self.obj_router, external_gateway_info={
            'network_id': public_network.id
        })
        LOGGER.info(f"Router '{self.obj_router.name}' gateway set to external network: {public_network.name}")
        self.conn.network.add_interface_to_router(self.obj_router, subnet_id=subnet.id)
        LOGGER.info(f"Subnet '{subnet.name}' added to router '{self.obj_router.name}' as an interface")

        return self.obj_router

    def create_and_get_network(self) -> Network:
        if self.obj_network:
            return self.obj_network

        self.obj_network = self.conn.network.create_network(
            name=self.network_name,
            project_id=self.project.id,
            mtu=1342
        )
        LOGGER.info(
            f"Created network {self.obj_network.name}/{self.obj_network.id} in {self.project.name}/{self.project.id}")
        return self.obj_network

    def create_and_get_subnet(self) -> Subnet:
        if self.obj_subnet:
            return self.obj_subnet

        self.obj_subnet = self.conn.network.create_subnet(
            network_id=self.obj_network.id,
            project_id=self.project.id,
            name=self.network_name,
            cidr=get_config("project_ipv4_subnet", r"\d+\.\d+\.\d+\.\d+/\d\d"),
            ip_version="4",
            enable_dhcp=True,
        )
        LOGGER.info(
            f"Created subnet {self.obj_subnet.name}/{self.obj_subnet.id} in {self.project.name}/{self.project.id}")

        return self.obj_subnet

    def delete_network(self):

        if self.obj_router:
            ports = self.conn.network.ports(device_id=self.obj_router.id)
            for port in ports:
                if port.device_owner == 'network:router_interface':
                    self.conn.network.remove_interface_from_router(self.obj_router,
                                                                   subnet_id=port.fixed_ips[0]['subnet_id'])
                    LOGGER.warning(f"Removed interface from subnet: {port.fixed_ips[0]['subnet_id']}")
            self.conn.network.update_router(self.obj_router, external_gateway_info=None)
            LOGGER.warning(f"Removed gateway from router {self.obj_router.id}")
            self.conn.delete_router(self.obj_router)
            LOGGER.warning(f"Deleted router {self.obj_router.id}/{self.obj_router.name}")

        if not self.obj_network:
            return

        self.conn.network.delete_network(self.obj_network, ignore_missing=False)

        for subnet_id in self.obj_network.subnet_ids:
            try:
                subnet_obj = self.conn.get_subnet_by_id(subnet_id)
                if subnet_obj:
                    LOGGER.warning(f"Delete subnet {subnet_obj.name}")
                    self.conn.network.delete_subnet(subnet_obj, ignore_missing=False)
            except ResourceNotFound:
                LOGGER.warning(f"Already deleted subnet {subnet_id}")

        LOGGER.warning(f"Deleted network {self.obj_network.name} / {self.obj_network.id}")

    def create_and_get_ingress_security_group(self) -> SecurityGroup:
        if self.obj_ingress_security_group:
            return self.obj_ingress_security_group

        LOGGER.info(f"Creating ingress security group {self.security_group_name_ingress} for "
                    f"project {self.project.name}/{self.project.domain_id}")
        self.obj_ingress_security_group = self.conn.network.create_security_group(
            name=self.security_group_name_ingress,
            description="Security group to allow SSH access to instances"
        )
        self.conn.network.create_security_group_rule(
            security_group_id=self.obj_ingress_security_group.id,
            direction='ingress',
            ethertype='IPv4',
            protocol='icmp',
            remote_ip_prefix='0.0.0.0/0'
        )

        self.conn.network.create_security_group_rule(
            security_group_id=self.obj_ingress_security_group.id,
            direction='ingress',
            ethertype='IPv4',
            protocol='tcp',
            port_range_min=22,
            port_range_max=22,
            remote_ip_prefix='0.0.0.0/0'
        )
        return self.obj_ingress_security_group

    def create_and_get_egress_security_group(self) -> SecurityGroup:
        if self.obj_egress_security_group:
            return self.obj_egress_security_group

        LOGGER.info(f"Creating egress security group {self.security_group_name_egress} for "
                    f"project {self.project.name}/{self.project.domain_id}")
        self.obj_egress_security_group = self.conn.network.create_security_group(
            name=self.security_group_name_egress,
            description="Security group to allow outgoing access"
        )
        self.conn.network.create_security_group_rule(
            security_group_id=self.obj_egress_security_group.id,
            direction='egress',
            ethertype='IPv4',
            protocol='tcp',
            port_range_min=None,
            port_range_max=None,
            remote_ip_prefix='0.0.0.0/0'
        )
        self.conn.network.create_security_group_rule(
            security_group_id=self.obj_egress_security_group.id,
            direction='egress',
            ethertype='IPv4',
            protocol='icmp',
            remote_ip_prefix='0.0.0.0/0'
        )

        return self.obj_egress_security_group

class SCSLandscapeTestMachine:

    def __init__(self, conn: Connection, project: Project, machine_name: str,
                 security_group_name_ingress: str,
                 security_group_name_egress: str
                 ):
        self.conn = conn
        self.machine_name = machine_name
        self.root_password = get_config("admin_vm_password")
        self.security_group_name_ingress = security_group_name_ingress
        self.security_group_name_egress = security_group_name_egress
        self.project = project
        self.obj: Server | None = conn.compute.find_server(self.machine_name)

    def get_image_id_by_name(self, image_name):
        for image in self.conn.image.images():
            if image.name == image_name:
                return image.id
        return None

    def get_flavor_id_by_name(self, flavor_name):
        for flavor in self.conn.compute.flavors():
            if flavor.name == flavor_name:
                return flavor.id
        return None

    def delete_machine(self):
        LOGGER.warning(f"Deleting machine {self.machine_name} in project {self.project.name}/{self.project.domain_id}")
        self.conn.delete_server(self.obj.id)

    def wait_for_delete(self):
        self.conn.compute.wait_for_delete(self.obj)
        LOGGER.warning(f"Machine {self.machine_name} in {self.obj.project_id} is deleted now")

    def create_or_get_server(self, network: Network):

        if self.obj:
            LOGGER.info(f"Server {self.obj.name}/{self.obj.id} in domain {self.project.domain_id} already exists")
            return

        self.obj = self.conn.compute.create_server(
            name=self.machine_name,
            flavor_id=self.get_flavor_id_by_name(get_config("vm_flavor")),
            networks=[{"uuid": network.id}],
            admin_password=self.root_password,
            description="automatically created",
            block_device_mapping_v2=[{
               "boot_index": 0,
               "uuid": self.get_image_id_by_name(get_config("vm_image")),
               "source_type": "image",
               "destination_type": "volume",
               "volume_size": int(get_config("vm_volume_size_gb",r"\d+")),
               "delete_on_termination": True,
           }],
            key_name=KEYPAIR_NAME,
        )
        LOGGER.info(f"Created server {self.obj.name}/{self.obj.id} in project {network.project_id}/{network}")

    def add_floating_ip(self):
        public_network = self.conn.network.find_network('public')
        if not public_network:
            LOGGER.error("There is no 'public' network")
            return

        floating_ips = []
        if self.obj.addresses:
            for network_name, addresses in self.obj.addresses.items():
                for address in addresses:
                    if address['OS-EXT-IPS:type'] == 'floating':  # Check if the IP is a floating IP
                        floating_ips.append(address['addr'])

        if len(floating_ips) == 0:
            LOGGER.info(f"Add floating ip {self.obj.name}/{self.obj.id} in domain {self.project.domain_id}")
            self.wait_for_server()
            floating_ip = self.conn.network.create_ip(floating_network_id=public_network.id)
            server_port = list(self.conn.network.ports(device_id=self.obj.id))[0]
            self.conn.network.add_ip_to_port(server_port, floating_ip)
        else:
            LOGGER.info(
                f"Floating ip is already added to {self.obj.name}/{self.obj.id} in domain {self.project.domain_id}")

        sec_obj_ingress = self.conn.get_security_group(self.security_group_name_ingress)
        sec_obj_egress = self.conn.get_security_group(self.security_group_name_egress)

        sec_group_add_ingress = True
        sec_group_add_egress = True
        for sg in self.obj.security_groups:
            if sg["name"] == self.security_group_name_ingress:
                sec_group_add_ingress = False
                LOGGER.info(f"Security group is already added {self.security_group_name_ingress} to server")
            if sg["name"] == self.security_group_name_egress:
                sec_group_add_egress = False
                LOGGER.info(f"Security group is already added {self.security_group_name_egress} to server")

        if sec_group_add_ingress:
            LOGGER.info(f"Adding security group {self.security_group_name_ingress} to server")
            self.conn.compute.add_security_group_to_server(self.obj, sec_obj_ingress)

        if sec_group_add_egress:
            LOGGER.info(f"Adding security group {self.security_group_name_egress} to server")
            self.conn.compute.add_security_group_to_server(self.obj, sec_obj_egress)

    def wait_for_server(self):
        self.conn.compute.wait_for_server(self.obj)

    def start_server(self):
        if self.obj.status != 'ACTIVE':
            self.conn.compute.start_server(self.obj.id)
            LOGGER.info(f"Server '{self.obj.name}' started successfully.")
        else:
            LOGGER.info(f"Server '{self.obj.name}' is already running.")

    def stop_server(self):
        if self.obj.status == 'ACTIVE':
            self.conn.compute.stop_server(self.obj.id)
            LOGGER.info(f"Server '{self.obj.name}' started successfully.")
        else:
            LOGGER.info(f"Server '{self.obj.name}' is already running.")


class SCSLandscapeTestProject:

    def __init__(self, admin_conn: Connection, project_name: str, domain: Domain,
                 user: SCSLandscapeTestUser):
        self._admin_conn = admin_conn
        self._project_conn: Connection | None = None
        self.project_name = project_name
        self.security_group_name_ingress = f"ingress-ssh-{project_name}"
        self.security_group_name_egress = f"egress-any-{project_name}"
        self.domain = domain
        self.user = user
        self.obj: Project = self._admin_conn.identity.find_project(project_name, domain_id=self.domain.id)
        self.scs_network: SCSLandscapeTestNetwork | None = \
            SCSLandscapeTestProject._get_network(admin_conn, self.obj,
                                                 self.security_group_name_ingress,
                                                 self.security_group_name_egress
                                                 )
        self.scs_machines: list[SCSLandscapeTestMachine] = \
            SCSLandscapeTestProject._get_machines(admin_conn, self.obj,
                                                  self.security_group_name_ingress,
                                                  self.security_group_name_egress
                                                  )
        self.ssh_key: Keypair | None = None

    @property
    def project_conn(self) -> Connection:
        if self._project_conn:
            return self._project_conn

        LOGGER.info(f"Establishing a connection for project {self.obj.name}/{self.obj.domain_id}")
        self._project_conn = self._admin_conn.connect_as(
            domain_id=self.obj.domain_id,
            project_id=self.obj.id,
            username=self.user.user_name,
            password=self.user.user_password,
        )
        return self._project_conn

    @staticmethod
    def _get_network(conn: Connection, obj: Project,
                     security_group_name_ingress: str,
                     security_group_name_egress: str,
                     ) -> None | SCSLandscapeTestNetwork:
        if not obj:
            return None
        return SCSLandscapeTestNetwork(conn, obj, security_group_name_ingress,security_group_name_egress)

    @staticmethod
    def _get_machines(conn: Connection, obj,
                      security_group_name_ingress: str,
                      security_group_name_egress: str,
                      ) -> list[SCSLandscapeTestMachine]:
        if not obj:
            return []
        result = []
        for server in conn.compute.servers(all_projects=True, project_id=obj.id):
            scs_server = SCSLandscapeTestMachine(conn, obj, server.name, security_group_name_ingress, security_group_name_egress)
            scs_server.obj = server
            result.append(scs_server)
        return result

    def get_role_id_by_name(self, role_name) -> str:
        for role in self._admin_conn.identity.roles():
            if role.name == role_name:
                return role.id
        raise RuntimeError(f"No such role {role_name}")

    def assign_role_to_user_for_project(self, role_name: str):
        self._admin_conn.identity.assign_project_role_to_user(
            user=self.user.obj.id, project=self.obj.id, role=self.get_role_id_by_name(role_name))
        LOGGER.info(f"Assigned {role_name} to {self.user.obj.id} for "
                    f"project {self.obj.id}/{self.obj.domain_id}")

    def assign_role_to_global_admin_for_project(self, role_name: str):
        user_id = self._admin_conn.session.get_user_id()
        self._admin_conn.identity.assign_project_role_to_user(
            user=user_id, project=self.obj.id, role=self.get_role_id_by_name(role_name))
        LOGGER.info(f"Assigned global admin {role_name} to {user_id} for project {self.obj.id}{self.obj.domain_id}")

    def adapt_quota(self):
        current_quota =  self._admin_conn.compute.get_quota_set(self.obj.id)
        new_quota = {}
        if "compute_quotas" in CONFIG:
            for key_name in CONFIG["compute_quotas"].keys():
                try:
                    current_value = getattr(current_quota, key_name)
                except AttributeError:
                    LOGGER.error(f"No such compute quota field {key_name}")
                    sys.exit()
                new_value = int(get_config(key_name, r"\d+", parent_key="compute_quotas", default=str(getattr(current_quota, key_name))))
                if current_value != new_value:
                    LOGGER.info(f"New compute quota for project: {self.obj.id} in domain {self.domain.name}/{self.domain.id} "
                                f": {key_name} : {current_value} -> {new_value}")
                    new_quota[key_name] = new_value
        if len(new_quota):
            self._admin_conn.set_compute_quotas(self.obj.id, **new_quota)
            LOGGER.info(f"Configured compute quotas for project: {self.obj.id} in domain {self.domain.name}")
        else:
            LOGGER.info(f"Configured compute quotas for project {self.obj.id} in domain {self.domain.name} not changed")

    def create_and_get_project(self) -> Project:
        if self.obj:
            self.adapt_quota()
            self.scs_network = SCSLandscapeTestNetwork(self._admin_conn, self.obj, self.security_group_name_ingress, self.security_group_name_egress)
            self.scs_network.create_and_get_network_setup()
            return self.obj

        self.obj = self._admin_conn.identity.create_project(
            name=self.project_name,
            domain_id=self.domain.id,
            description="Auto generated",
            enabled=True
        )
        LOGGER.info(f"Created project: {self.obj.id} in domain {self.domain.name}/{self.domain.id}")
        self.adapt_quota()

        self.assign_role_to_user_for_project("manager")
        self.assign_role_to_user_for_project("load-balancer_member")
        self.assign_role_to_user_for_project("member")

        self.scs_network = SCSLandscapeTestNetwork(self.project_conn, self.obj, self.security_group_name_ingress, self.security_group_name_egress)
        self.scs_network.create_and_get_network_setup()

        return self.obj

    def delete_project(self):

        ##########################################################################################
        ## CLEANUP THE PROJECT
        for scs_machine in self.scs_machines:
            scs_machine.delete_machine()

        for scs_machine in self.scs_machines:
            scs_machine.wait_for_delete()

        self.scs_network.delete_network()

        LOGGER.warning(f"Cleanup of project {self.obj.name}/{self.obj.id} in domain {self.domain.name}{self.domain.id}")
        self.project_conn.project_cleanup(dry_run=False, wait_timeout=300)
        ## This function before this line should do all the steps above, but because of a bug this
        ## does not work as expected currently
        ## TODO: add bug report reference
        ##########################################################################################

        LOGGER.warning(f"Deleting project {self.obj.name} in domain {self.domain.name}/{self.domain.id}")
        ##########################################################################################
        ## DELETE THE PROJECT
        ## The following function should also the steps beyond
        ## TODO: add bug report reference
        self._admin_conn.identity.delete_project(self.obj.id)

        # Delete the security groups after deleting the project because the "default" security
        # group not seems to be deletable when the project exists
        for sg in self._admin_conn.network.security_groups(project_id=self.obj.id):
            LOGGER.warning(f"Deleting security group: {sg.name} ({sg.id})")
            self._admin_conn.network.delete_security_group(sg.id)
        ##########################################################################################

    def get_and_create_machines(self, machines: list[str]):

        sorted_machines = sorted(machines)

        for nr, machine_name in enumerate(sorted_machines):
            machine = SCSLandscapeTestMachine(self.project_conn, self.obj, machine_name, self.security_group_name_ingress, self.security_group_name_egress)
            machine.create_or_get_server(self.scs_network.obj_network)
            if nr == 0:
                machine.add_floating_ip()
            self.scs_machines.append(machine)

    def get_or_create_ssh_key(self):
        self.ssh_key = self.project_conn.compute.find_keypair(KEYPAIR_NAME)
        if not self.ssh_key:
            LOGGER.info(f"Create SSH keypair '{KEYPAIR_NAME} in project {self.obj.name} in "
                        f"domain {self.domain.name}")
            self.ssh_key = self.project_conn.compute.create_keypair(
                name=KEYPAIR_NAME,
                public_key="\n".join(get_config("admin_vm_ssh_key", r"ssh-\S+\s\S+\s\S+", multi_line=True)),
            )


class SCSLandscapeTestDomain:

    def __init__(self, conn: Connection, domain_name: str):
        self.conn = conn
        self.domain_name = domain_name
        self.obj: Domain = self.conn.identity.find_domain(domain_name)
        self.scs_user = SCSLandscapeTestDomain._get_user(conn, domain_name, self.obj)
        self.scs_projects: dict[str, SCSLandscapeTestProject] = SCSLandscapeTestDomain._get_projects(
            conn, self.obj, self.scs_user)

    @staticmethod
    def _get_user(conn: Connection, domain_name: str, obj: Domain):
        if not obj:
            return None
        return SCSLandscapeTestUser(conn, f"{domain_name}-admin", obj)

    @staticmethod
    def _get_projects(conn: Connection, domain: Domain | None, user: SCSLandscapeTestUser | None) \
            -> dict[str, SCSLandscapeTestProject]:
        if not domain or not user:
            return dict()
        result: dict[str, SCSLandscapeTestProject] = dict()
        for project in conn.identity.projects(domain_id=domain.id):
            result[project.name] = SCSLandscapeTestProject(conn, project.name, domain, user)
        return result

    def create_and_get_domain(self) -> Domain:
        if self.obj:
            return self.obj

        self.obj = self.conn.identity.create_domain(
            name=self.domain_name,
            description="Automated creation",
            enabled=True
        )
        LOGGER.info(f"Created domain {self.obj.name} / {self.obj.id}")
        self.scs_user = SCSLandscapeTestDomain._get_user(self.conn, self.domain_name, self.obj)
        return self.obj

    def disable_domain(self):
        domain = self.conn.identity.update_domain(self.obj.id, enabled=False)
        return domain

    def delete_domain(self):
        if self.obj is None:
            return

        for project in self.scs_projects.values():
            project.delete_project()

        self.scs_user.delete_user()
        self.disable_domain()
        domain = self.conn.identity.delete_domain(self.obj.id)
        LOGGER.warning(f"Deleted domain: {self.obj.id}, Name: {self.obj.name}")
        self.obj = None
        return domain

    def create_and_get_projects(self, create_projects: list[str]):
        self.scs_user.create_and_get_user()

        for project_name in create_projects:
            project = SCSLandscapeTestProject(self.conn, project_name, self.obj, self.scs_user)
            project.create_and_get_project()
            project.get_or_create_ssh_key()
            self.scs_projects[project_name] = project

    def create_and_get_machines(self, machines: list[str]):
        for project in self.scs_projects.values():
            project.get_and_create_machines(machines)
