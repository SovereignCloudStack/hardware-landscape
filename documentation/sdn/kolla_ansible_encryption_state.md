---
title: Kolla Ansible Encryption state
tags: kolla kolla-ansible openstack security
---

# Kolla Ansible control plane security

For Kolla Ansible SCS lists 18 supported services (APIs) as part of a compliant
Open Stack deployment. There are also a couple of support tools deployed like
database (MariaDB), cache service (Redis), message broker (RabbitMQ), virtual
networking components (Open vSwitch) and virtualization manager for compute
(libvirt). They communicate mostly through REST APIs on internal virtual
networks. This control plane traffic is of security concern. Most of the
services and tools support TLS encryption and there have been some efforts to
make this support accessible to operators of Kolla Ansible deployments. We
analyzed the state of encryption in current version of Kolla Ansible (2024.1
Series) and prepared upstream contributions to complete the control plane
traffic encryption coverage.

## Current state of control plane encryption

![](https://input.scs.community/uploads/7f141b31-d23c-498f-ae0b-ac74127c7ce4.png)
[This table](https://scs.sovereignit.de/nextcloud/s/G4DzznMKeJHqMBx)
shows current state of the encryption support, vertically we have
services and tools used and horizontally communication channels they are using.
Green cells show encryption already supported in Kolla Ansible, yellow ones are
the new contributions to the project currently on review. Grey cells are just
combinations which do not communicate in real deployment. There is also a
more
[detailed table version](https://scs.sovereignit.de/nextcloud/s/G4DzznMKeJHqMBx)
containing also the contribution links.

Kolla Ansible currently divides the communication channels into 3 categories -
internal, external and backend. Internal and external are both API client to
proxy communications, between services on internal networks and external
clients to proxy respectively. Settings for encrypting these path are mostly
present. Backend communication besides the proxy to service path encompasses
various intra-service channels like database cluster replication, message
broker traffic or compute service (Nova) using virtualization manager (libvirt)
to manage compute instances.

## Upstream proposals

To cover found gaps we prepared more than 20 new change requests to Kolla
Ansible and Kolla projects, which add the possibility for the operator to
encrypt these backend communication channels using TLS. Some of these updates
are part of and dependent on broader technology shifts. To reliably implement
backend TLS Kolla Ansible will start using ProxySQL for database access and
Redis as caching backend. Thorough analysis enabled us also to find missing
support in existing options and fix it, like enabling TLS security for libvirt
virtualization API for Nova compute service rendered instance monitor part of
Masakari (High Availability for compute) unable to function.

[Implement TLS for Redis](https://review.opendev.org/c/openstack/kolla-ansible/+/909188)
[Fix HAProxy TLS config when only backend TLS enabled](https://review.opendev.org/c/openstack/kolla-ansible/+/926894)
[Fix Masakari instancemonitor when libvirt TLS enabled](https://review.opendev.org/c/openstack/kolla-ansible/+/929594)
[Add backend to kolla_externally_managed_cert behaviour](href="https://review.opendev.org/c/openstack/kolla-ansible/+/927853)
[Add certificates for RabbitMQ internode TLS](https://review.opendev.org/c/openstack/kolla-ansible/+/921380)
[Enable backend TLS for Manila](https://review.opendev.org/c/openstack/kolla-ansible/+/927725)
[Add support for RabbitMQ internode tls](https://review.opendev.org/c/openstack/kolla-ansible/+/921381)
[Add Redis as caching backend for Heat](https://review.opendev.org/c/openstack/kolla-ansible/+/909224)
[Add Redis as caching backend for Ceilometer](https://review.opendev.org/c/openstack/kolla-ansible/+/926721)
[Add caching options](https://review.opendev.org/c/openstack/kolla-ansible/+/927104)
[Add Redis as caching backend for Placement](https://review.opendev.org/c/openstack/kolla-ansible/+/909222)
[Add Redis as caching backend for Keystone](https://review.opendev.org/c/openstack/kolla-ansible/+/909201)
[Add Redis as caching backend for Nova](https://review.opendev.org/c/openstack/kolla-ansible/+/909203)
[Add backend TLS encryption between RabbitMQ management and HAProxy](https://review.opendev.org/c/openstack/kolla-ansible/+/919086)
[Change Manila container user to root](https://review.opendev.org/c/openstack/kolla/+/927722)
[Add backend TLS encryption for Gnocchi](https://review.opendev.org/c/openstack/kolla-ansible/+/927229)
[Add backend TLS encryption for Masakari](https://review.opendev.org/c/openstack/kolla-ansible/+/927228)
[Add backend TLS encryption for CloudKitty](https://review.opendev.org/c/openstack/kolla-ansible/+/927230)
[CI: Fix upgrade jobs failing on adding new certificates](https://review.opendev.org/c/openstack/kolla-ansible/+/926284)
[Add backend TLS encryption of MariaDB replication and SST traffic](https://review.opendev.org/c/openstack/kolla-ansible/+/925317)
[Add documentation for caching](https://review.opendev.org/c/openstack/kolla-ansible/+/918285)
[Patch service-cert-copy role to be used w/o HAProxy](https://review.opendev.org/c/openstack/kolla-ansible/+/915901)

# Kolla Ansible data plane security

In parallel to the control plane traffic security we looked also on the data
plane encryption. In most cases customer compute instances need to communicate
and the operator should have the possibility to simply and transparently secure
this traffic. Network tenant isolation is already built in OpenStack
networking, confidentiality is another issue as it depends on the underlaying
infrastructure. In more complex deployments part of the physical networking can
be untrusted and could potentialy be a security weakness. The analysis is
described in an
[ADR](https://github.com/SovereignCloudStack/standards/blob/main/Drafts/node-to-node-encryption.md).

## Transparent IPsec encryption

Due to emphasis on scalable software defined networking OVN (Open Virtual
Network) is already a popular choice for networking agent in OpenStack and as
it uses tunneling for the transport of compute traffic a natural solution to
the security of that traffic is the encryption of these tunnels. We implemented
a transparent IPsec encryption service as IPsec is a time tested standard and
is already a part of the Open vSwitch project implementation used in OpenStack.
The service works automatic, as the monitor process reacts to events in the OVN
networking. We proposed this service to Kolla and Kolla Ansible projects.

## Upstream proposals

[Kolla IPsec service image](https://review.opendev.org/c/openstack/kolla/+/930804)
[Kolla Ansible IPsec role](https://review.opendev.org/c/openstack/kolla-ansible/+/930841)
