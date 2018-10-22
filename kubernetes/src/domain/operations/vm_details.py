from typing import Dict

from logging import Logger
from model.clients import KubernetesClients
from model.deployed_app import DeployedAppResource
from domain.services.networking import KubernetesNetworkingService
from domain.services.deployment import KubernetesDeploymentService
from domain.services.vm_details import VmDetailsProvider


class VmDetialsOperation(object):
    def __init__(self, networking_service, deployment_service, vm_details_service):
        """
        :param VmDetailsProvider vm_details_service:
        :param KubernetesNetworkingService networking_service:
        :param KubernetesDeploymentService deployment_service:
        """
        self.vm_details_service = vm_details_service
        self.deployment_service = deployment_service
        self.networking_service = networking_service

    def create_vm_details_bulk(self, logger, clients, items):
        """

        :param Logger logger:
        :param KubernetesClients clients:
        :param Dict items:
        :return:
        """
        result = []
        for item in items['items']:
            deployed_app = DeployedAppResource(deployed_app_dict=item['deployedAppJson'])

            services = self.networking_service.get_services_by_app_name(clients=clients,
                                                                        namespace=deployed_app.namespace,
                                                                        app_name=deployed_app.kubernetes_name)

            deployment = self.deployment_service.get_deployment_by_name(clients=clients,
                                                                        namespace=deployed_app.namespace,
                                                                        app_name=deployed_app.kubernetes_name)

            result.append(
                self.vm_details_service.create_vm_details(services=services,
                                                          deployment=deployment,
                                                          deployed_app=deployed_app,
                                                          deploy_app_name=deployed_app.cloudshell_resource_name))

        return result
