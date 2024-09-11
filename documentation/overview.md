# Turnkey solution

## Scope of this document

The Sovereign Cloud Stack software (reference implementation) consists of numerous modules. This is intentional, as we have various operators that have deployed preexisting technology or have specific requirements and expect SCS to fit into it. It is good practice to build technology in a modular way, as this allows different pieces to move at its own speed and ensures that work is invested into proper abstractions and interfaces to build a losely coupled system that is resilient.

That said, the most value is derived by operators that consume the complete stack. We thus provide an overview over all components and some hints of how to deploy them.

We start with the functional stack at the bottom, where a deployment on server hardware is automated.

## Overview table
| Layer | Component | Subcomponent | Purpose | Status | Requirements | Documentation |
|--|--|--|--|--|--|--|
| Infra | OSISM | Manager, Netbox, ... | Lifecycle Manage deployment | Prod | HW | https://docs.scs.community/docs/iaas/guides/configuration-guide/ |
| Ops | OSISM | Prometheus, Netdata, AlertMgr, ... | Monitor Infra layer | Prod | HW | https://docs.scs.community/docs/iaas/guides/concept-guide/#components-in-a-cluster |
| SDS | OSISM | ceph | Storage (Block, Object) | Prod | HW | https://docs.scs.community/docs/iaas/guides/concept-guide/components/ceph |
| SDN | OSISM | OVN | Networking | Prod | HW | https://docs.scs.community/docs/iaas/guides/concept-guide/components/sonic#-lifecycle-management-of-open-virtual-network-ovn-in-osism |
| IaaS | OSISM | OpenStack | Virtualization | Prod | HW | https://docs.scs.community/docs/iaas/guides/concept-guide/components/openstack |
| KaaS | ClusterStacks | CAPI, CAPO, ClusterStacks, CSO, CSPO  | K8s cluster management | Stable | IaaS | https://docs.scs.community/docs/container/components/cluster-stacks/components/cluster-stacks/overview |
| PaaS | Registry | harbor | Container registry | Prod | KaaS | https://docs.scs.community/docs/category/container-registry |
| API | Central API | Central API | API for IAM, IaaS, KaaS | Tech Preview | KaaS | https://scs.community/tech/2024/08/13/central-api-tech-preview-release/ |
| Ops | OS Health Monitor | OSHM (old) | IaaS monitor | Deprecated | IaaS | https://docs.scs.community/docs/operating-scs/guides/openstack-health-monitor/Debian12-Install |
| Ops | Health Monitor | OSHM (new) | IaaS monitor | Stable | IaaS | https://docs.scs.community/docs/category/scs-health-monitor |
| Ops | Health Monitor | SCS monitoring | K8s cluster monitor | Prod | KaaS | https://docs.scs.community/docs/category/monitoring |
| Ops | Status Page | SCS Status Page | Publication of platform status | Technical Preview | KaaS | https://docs.scs.community/docs/category/status-page |
| Ops | Metering | SCS metering | Usage data collection | Tech Preview | IaaS | https://docs.scs.community/docs/category/metering |
| Ops | SCS Compliance | SCS compliance tests | Testsuite | Stable | IaaS+KaaS | https://docs.scs.community/standards/scs-0004-v1-achieving-certification |
| CI | SCS pipelines | zuul | Automation and validation | Stable | IaaS (KaaS optional) | https://docs.scs.community/community/tools/zuul |
| Sec | Pentesting | SCS Pentesting | Automated security assessent | Stable | zuul | https://docs.scs.community/docs/operating-scs/components/automated-pentesting-iaas/overview#scs-automated-pentesting |
| IAM | Keycloak | Keycloak | ID provider and broker for federation | Stable | IaaS | https://docs.scs.community/contributor-docs/operations/iam/identity-federation-in-scs |

Legend for status:
* Prod = Proven in numerous production environments
* Stable = Stable release, fully supported, may not be removed without prior deprecation
* Tech Preview = Technical preview, may not be depended upon yet and may undergo significant change or removal in the future
* Deprecated = Still supported, but to be removed in the future

Notes:
* OSISM comes with numerous components to manage the hardware deployment of the Infra and IaaS stack, such as homer (the portal), ARA, netbox, netdata, ... which are not all listed here. Their deployment is covered with a standard OSISM deployment and thus no separate deployment guides are linked here.
* Similarly, Cluster Stacks, building on top of Kubernetes Cluster API, consists of a set of components that are all meant to be used together and are thus covered in one set of documents. This also includes the cluster-add-ons to integrate with the underlaying IaaS. Note that while Cluster Stack has been designed and implemented to work very well on SCS IaaS, it does also fully support other IaaS environments (such as e.g. docker for development or Hetzner for production).
* The journey to provide seamless self-service federation across all layers of the SCS stack is a long one; while the IAM solution included is stable, it is still limited in scope, which has prevented broad adoption thus far. Work is underway to address this, which is reflected in the linked documentation.
