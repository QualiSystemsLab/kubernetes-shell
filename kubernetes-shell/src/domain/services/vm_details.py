from cloudshell.cp.core.utils import first_or_default
from kubernetes.client import V1Service, AppsV1beta1Deployment
from typing import List

from cloudshell.cp.core.models import VmDetailsData, VmDetailsProperty

from domain.services.tags import TagsService
from model.deployed_app import DeployedAppResource


class VmDetailsProvider(object):
    def __init__(self):
        pass

    def create_vm_details(self, services, deployment, deployed_app=None, deploy_app_name=""):
        """
        :param List[V1Service] services:
        :param AppsV1beta1Deployment deployment:
        :param str deploy_app_name:
        :return:
        """
        vm_instance_data = self._get_vm_instance_data(services, deployment, deployed_app)

        return VmDetailsData(vmInstanceData=vm_instance_data,
                             vmNetworkData=None,
                             appName=deploy_app_name)

    def _get_vm_instance_data(self, services, deployment, deployed_app):
        """
        :param List[V1Service] services:
        :param AppsV1beta1Deployment deployment:
        :param DeployedAppResource deployed_app:
        :return:
        """

        internal_service, external_service = self._get_internal_external_services_set(services)

        data = [VmDetailsProperty(key='Image', value=self._get_image(deployment)),
                VmDetailsProperty(key='Replicas', value=self._get_replicas(deployment, deployed_app)),
                VmDetailsProperty(key='Ready Replicas', value=self._get_ready_replicas(deployment)),
                VmDetailsProperty(key='Internal IP', value=self._get_internal_ip(internal_service)),
                VmDetailsProperty(key='Internal Ports', value=self._get_service_ports(internal_service)),
                VmDetailsProperty(key='External IP', value=self._get_external_ip(external_service)),
                VmDetailsProperty(key='External Ports', value=self._get_external_service_ports(external_service)),
                ]

        return data

    def _get_internal_external_services_set(self, services):
        if services:
            internal_service = \
                first_or_default(services, lambda x: x.metadata.labels.get(TagsService.INTERNAL_SERVICE, False))

            external_service = \
                first_or_default(services, lambda x: x.metadata.labels.get(TagsService.EXTERNAL_SERVICE, False))

            return internal_service, external_service

        return None, None

    def _get_internal_ip(self, internal_service):
        if internal_service:
            return internal_service.spec.cluster_ip
        else:
            return ''

    def _get_external_ip(self, external_service):
        if not external_service:
            return ''

        try:
            return ', '.join([x.ip for x in external_service.status.load_balancer.ingress])
        except:
            try:
                return ','.join([x.hostname for x in external_service.status.load_balancer.ingress])
            except:
                try:
                    return ', '.join([x.ip for x in external_service.spec.load_balancer_ip])
                except:
                    return ''

    def _get_service_ports(self, internal_service):
        if internal_service:
            return ', '.join([str(port.port) for port in internal_service.spec.ports])
        else:
            return ''

    def _get_external_service_ports(self, external_service):
        if external_service:
            return ', '.join(
                ['{port}:{node_port}'.format(port=str(port.port), node_port=str(port.node_port))
                 if port.node_port and external_service.spec.type == 'NodePort' else str(port.port)
                 for port in external_service.spec.ports])
        else:
            return ''

    def _get_replicas(self, deployment, deployed_app):
        return deployed_app.replicas if deployed_app else deployment.spec.replicas

    def _get_ready_replicas(self, deployment):
        return deployment.status.ready_replicas if deployment.status.ready_replicas else '0'

    def _get_image(self, deployment):
        images = list(set([c.image for c in deployment.spec.template.spec.containers]))
        return ', '.join(images)
