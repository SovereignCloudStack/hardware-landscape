
from openstack import connection
from openstack.config import loader

class OpenstackLandscape:

    def __init__(self, cloud_config_name: str = "vp18"):
        config = loader.OpenStackConfig()
        cloud_config = config.get_one(cloud_config_name)
        self.conn = connection.Connection(config=cloud_config)

    def assign_role_to_user(self, user_id: str, domain_id: str, role_name):
        role = None
        for r in self.conn.identity.roles():
            if r.name == role_name:
                role = r
                break
        if not role:
            raise ValueError(f"Role '{role_name}' not found")

        self.conn.identity.assign_project_role_to_user(user_id, domain_id, role.id)
        print(f"Assigned role '{role_name}' to user '{user_id}' in domain '{domain_id}'")

    def create_user_in_domain(self, domain_id: str, username: str, password: str, email: str = None):
        user = self.conn.identity.create_user(
            name=username,
            password=password,
            email=email,
            domain_id=domain_id,
            enabled=True
        )
        self.assign_role_to_user(user.id, user.domain_id, "manager")
        print(f"Created user: {user.id}, Name: {user.name}, Domain ID: {user.domain_id}")
        return user

    def create_domain(self, domain_name: str, description: str, create_projects: list[str], create_vms: list[str]):
        domain = self.conn.identity.create_domain(
            name=domain_name,
            description=description,
            enabled=True
        )
        print(f"Created domain: {domain.id}, Name: {domain.name}")

        user = self.create_user_in_domain(domain.id, f"{domain_name}-admin", "yolobanana")

        for create_project_name in create_projects:
            self.create_project(create_project_name, domain, user.id, create_vms)

        return domain

    def get_role_id_by_name(self, role_name) -> str:
        for role in self.conn.identity.roles():
            if role.name == role_name:
                return role.id
        raise RuntimeError(f"No such role {role_name}")

    def assign_role_to_user_for_project(self, user_id, project_id: str, role_name: str):
        self.conn.identity.assign_project_role_to_user(
            user=user_id, project=project_id, role=self.get_role_id_by_name(role_name))
        print(f"Assigned {role_name} to {user_id} for project {project_id}")

    def create_network_setup(self, project):
        network = self.conn.network.create_network(
            name=f"localnet-{project.name}",
            project_id=project.id,
            mtu=1342
        )
        print(f"Created {network.name} with {network.id} in {project.name}")

        subnet = self.conn.network.create_subnet(
            network_id=network.id,
            project_id=project.id,
            name=f"localsubnet-{project.name}",
            cidr="192.168.200.0/24",
            ip_version="4",
            enable_dhcp=True,
        )
        print(f"Created {subnet.name} in {project.name}")
        return network

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
            #project_id=project.id
        )
        print(f"Created server {server.name} in project {network.project_id}")

    def create_project(self, create_project_name: str , domain: str, user_id: str, create_vms: list[str]):
        project = self.conn.identity.create_project(
            name=create_project_name,
            domain_id=domain.id,
            description="Auto generated",
            enabled=True
        )
        print(f"Created project: {project.id}, Name: {project.name}, Domain ID: {project.domain_id}")
        self.assign_role_to_user_for_project(user_id, project.id, "manager")
        self.assign_role_to_user_for_project(user_id, project.id, "load-balancer_member")
        self.assign_role_to_user_for_project(user_id, project.id, "member")

        network = self.create_network_setup(project)

        for server in create_vms:
            self.create_server(server, network, project)

    def get_domain_id_by_name(self, domain_name) -> str:
        for domain in self.conn.identity.domains():
            if domain.name == domain_name:
                return domain.id
        raise ValueError(f"Domain '{domain_name}' not found")

    def disable_domain(self, domain_name):
        domain = self.conn.identity.update_domain(domain_name, enabled=False)
        return domain

    def delete_domain(self, domain_name: str):
        domain_id = self.get_domain_id_by_name(domain_name)
        self.disable_domain(domain_id)
        domain = self.conn.identity.delete_domain(domain_id)
        print(f"Deleted domain: {domain_id}, Name: {domain_name}")
        return domain
