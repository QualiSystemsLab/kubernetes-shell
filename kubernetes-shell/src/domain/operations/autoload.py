import data_model
from domain.services.clients import ApiClientsProvider

from model.clients import KubernetesClients
from model.deployed_app import DeployedAppResource
from domain.services.deployment import KubernetesDeploymentService


class AutolaodOperation(object):

    def __init__(self, api_clients_provider, deployment_service):
        """
        :param KubernetesDeploymentService deployment_service:
        :param ApiClientsProvider api_clients_provider:
        """
        self.deployment_service = deployment_service
        self.api_clients_provider = api_clients_provider

    def validate_cloud_provider_resource_config(self, cloud_provider_resource):
        """
        :param data_model.Kubernetes cloud_provider_resource:
        :return:
        """

        # create api clients by cluster name
        clients = self.api_clients_provider.get_api_clients(cloud_provider_resource)

        # list nodes and make sure we have 1 or more nodes just to check authentication works
        nodes = clients.core_api.list_node(watch=False)
        if not nodes or len(nodes.items) < 1:
            raise ValueError("Cluster '{}' has zero (0) nodes".format(cloud_provider_resource.cluster_name))

    def get_deployed_app_autoload_data(self, clients, deployed_app):
        """
        :param KubernetesClients clients:
        :param DeployedAppResource deployed_app:
        :return:
        """
        pods = self.deployment_service.get_pods_by_name(clients,
                                                        deployed_app.namespace,
                                                        deployed_app.kubernetes_name)
        result = []
        for pod in pods:
            result.append({'PodIP': pod.status.pod_ip})

        return result
