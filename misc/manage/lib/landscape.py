from openstack import connection
from openstack.identity.v3.domain import Domain
from openstack.identity.v3.project import Project
from openstack.identity.v3.user import User
from openstack.network.v2.network import Network
from openstack.network.v2.subnet import Subnet


class SCSLandscapeTestNetwork:

    def __init__(self, conn: connection.Connection, project: Project):
        self.conn = conn
        self.project: Project = project
        self.network_name = f"localnet-{self.project.name}"
        self.subnet_name = f"localsubnet-{self.project.name}"
        self.obj_network: Network | None = SCSLandscapeTestNetwork._find_network(self.network_name, conn, project)
        self.obj_subnet: Subnet | None = SCSLandscapeTestNetwork._find_subnet(self.network_name, conn, project)

    @staticmethod
    def _find_network(name, conn, project) -> Network | None:
        networks = [network for network in conn.network.networks(name=name, project_id=project.id)]
        if len(networks) == 0:
            return None
        elif len(networks) == 1:
            print(f"Loaded network {networks[0].name}")
            return networks[0]
        else:
            raise RuntimeError(f"More the one network with the name {name} in {project.name}")

    @staticmethod
    def _find_subnet(name, conn, project) -> Network | None:
        subnet = [network for network in conn.network.subnets(name=name, project_id=project.id)]
        if len(subnet) == 0:
            return None
        elif len(subnet) == 1:
            print(f"Loaded subnet {subnet[0].name}")
            return subnet[0]
        else:
            raise RuntimeError(f"More the one subnet with the name {name} in {project.name}")

    def create_and_get_network_setup(self) -> Network:
        network = self.create_and_get_network()
        self.create_and_get_subnet()
        return network

    def create_and_get_network(self):
        if self.obj_network:
            return self.obj_network

        self.obj_network = self.conn.network.create_network(
            name=self.network_name,
            project_id=self.project.id,
            mtu=1342
        )
        print(f"Created {self.obj_network.name} with {self.obj_network.id} in {self.project.name}")
        return self.obj_network

    def create_and_get_subnet(self):
        if self.obj_subnet:
            return self.obj_subnet

        self.obj_subnet = self.conn.network.create_subnet(
            network_id=self.obj_network.id,
            project_id=self.project.id,
            name=self.network_name,
            cidr="192.168.200.0/24",
            ip_version="4",
            enable_dhcp=True,
        )
        print(f"Created {self.obj_subnet.name} in {self.project.name}")
        return self.obj_subnet

    def delete_network(self):
        for subnet in self.obj_network.subnet_ids:
            self.conn.network.delete_subnet(subnet, ignore_missing=False)
            print(f"Deleted subnet {subnet}")
        self.conn.network.delete_network(self.obj_network, ignore_missing=False)
        print(f"Deleted network {self.obj_network.name} / {self.obj_network.id}")


class SCSLandscapeTestMachine:

    def __init__(self, conn: connection.Connection):
        self.conn = conn

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

    def create_server(self, server_name: str, network, project):
        server = self.conn.compute.create_server(
            name=server_name,
            flavor_id=self.get_flavor_id_by_name("SCS-1L-1"),
            image_id=self.get_image_id_by_name("Ubuntu 24.04"),
            networks=[{"uuid": network.id}],
            # project_id=project.id
        )
        print(f"Created server {server.name} in project {network.project_id}")


class SCSLandscapeTestUser:

    def __init__(self, conn: connection.Connection, user_name: str, domain: Domain):
        self.conn = conn
        self.user_name = user_name
        self.domain = domain
        self.obj = self.conn.identity.find_user(user_name, query={"domain_id": self.domain.id})

    def assign_role_to_user(self, role_name: str):
        self.conn.identity.assign_project_role_to_user(self.obj.id, self.domain.id, self.get_role_id_by_name(role_name))
        print(f"Assigned role '{role_name}' to user '{self.obj.name}' in domain '{self.domain.id}'")

    def create_and_get_user(self) -> User:

        if self.obj:
            return self.obj

        self.obj = self.conn.identity.create_user(
            name=self.user_name,
            password="yolobanana",
            domain_id=self.domain.id,
            enabled=True
        )
        self.assign_role_to_user("manager")
        print(f"Created user {self.obj.name} / {self.obj.id} with password {self.obj.password} in {self.domain.name}")
        return self.obj

    def delete_user(self):
        if not self.obj:
            return
        user = self.conn.identity.delete_user(self.obj.id)
        print(f"Deleted user: {self.obj.name} / {self.obj.id}")
        self.obj = None

    def get_role_id_by_name(self, role_name) -> str:
        for role in self.conn.identity.roles():
            if role.name == role_name:
                return role.id
        raise RuntimeError(f"No such role {role_name}")


class SCSLandscapeTestProject:

    def __init__(self, conn: connection.Connection, project_name: str, domain: Domain, user: User):
        self.conn = conn
        self.project_name = project_name
        self.domain = domain
        self.user = user
        self.obj: Project = self.conn.identity.find_project(project_name, domain_id=self.domain.id)
        self.scs_network: SCSLandscapeTestNetwork | None = SCSLandscapeTestProject._get_network(conn, self.obj)

    @staticmethod
    def _get_network(conn: connection.Connection, obj) -> None | SCSLandscapeTestNetwork:
       if not obj:
           return None
       return SCSLandscapeTestNetwork(conn, obj)

    def get_role_id_by_name(self, role_name) -> str:
        for role in self.conn.identity.roles():
            if role.name == role_name:
                return role.id
        raise RuntimeError(f"No such role {role_name}")

    def assign_role_to_user_for_project(self, role_name: str):
        self.conn.identity.assign_project_role_to_user(
            user=self.user.id, project=self.obj.id, role=self.get_role_id_by_name(role_name))
        print(f"Assigned {role_name} to {self.user.id} for project {self.obj.id}")

    def create_and_get_project(self) -> Project:
        if self.obj:
            self.scs_network = SCSLandscapeTestNetwork(self.conn, self.obj)
            self.scs_network.create_and_get_network_setup()
            return self.obj

        self.obj = self.conn.identity.create_project(
            name=self.project_name,
            domain_id=self.domain.id,
            description="Auto generated",
            enabled=True
        )
        print(f"Created project: {self.obj.id} in domain {self.domain.name}")
        self.assign_role_to_user_for_project("manager")
        self.assign_role_to_user_for_project("load-balancer_member")
        self.assign_role_to_user_for_project("member")

        self.scs_network = SCSLandscapeTestNetwork(self.conn, self.obj)
        self.scs_network.create_and_get_network_setup()

        return self.obj

    def delete_project(self):
        self.scs_network.delete_network()
        self.conn.identity.delete_project(self.obj.id)
        print(f"Deleted project {self.obj.name} in domain {self.domain.name}")


class SCSLandscapeTestDomain:

    def __init__(self, conn: connection.Connection, domain_name: str):
        self.conn = conn
        self.domain_name = domain_name
        self.obj: Domain = self.conn.identity.find_domain(domain_name)
        self.scs_user = SCSLandscapeTestDomain._get_user(conn, domain_name, self.obj)
        self.scs_projects: list[SCSLandscapeTestProject] = SCSLandscapeTestDomain._get_projects(
            conn, self.obj, self.scs_user)

    @staticmethod
    def _get_user(conn: connection.Connection, domain_name: str, obj: Domain):
        if not obj:
            return None
        return SCSLandscapeTestUser(conn, f"{domain_name}-admin", obj)

    @staticmethod
    def _get_projects(conn: connection.Connection, domain: Domain | None, user: User | None) -> list[
        SCSLandscapeTestProject]:
        if not domain or not user:
            return []
        result: list[SCSLandscapeTestProject] = []
        for project in conn.identity.projects(domain_id=domain.id):
            result.append(SCSLandscapeTestProject(conn, project.name, domain, user))
        return result

    def create_and_get_domain(self) -> Domain:
        if self.obj:
            return self.obj

        self.obj = self.conn.identity.create_domain(
            name=self.domain_name,
            description="Automated creation",
            enabled=True
        )
        print(f"Created domain {self.obj.name} / {self.obj.id}")
        self.scs_user = SCSLandscapeTestDomain._get_user(self.conn, self.domain_name, self.obj)
        return self.obj

    def disable_domain(self):
        domain = self.conn.identity.update_domain(self.obj.id, enabled=False)
        return domain

    def delete_domain(self):
        if self.obj is None:
            return

        for project in self.scs_projects:
            project.delete_project()

        self.scs_user.delete_user()
        self.disable_domain()
        domain = self.conn.identity.delete_domain(self.obj.id)
        print(f"Deleted domain: {self.obj.id}, Name: {self.obj.name}")
        self.obj = None
        return domain

    def create_and_get_projects(self, create_projects: list[str]):
        user = self.scs_user.create_and_get_user()
        for project_name in create_projects:
            project = SCSLandscapeTestProject(self.conn, project_name, self.obj, user)
            project.create_and_get_project()
