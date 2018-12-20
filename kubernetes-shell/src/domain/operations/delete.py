from logging import Logger
from model.clients import KubernetesClients
from domain.services.deployment import KubernetesDeploymentService
from domain.services.networking import KubernetesNetworkingService


class DeleteInstanceOperation(object):
    def __init__(self, networking_service, deployment_service):
        """
        :param KubernetesNetworkingService networking_service:
        :param KubernetesDeploymentService deployment_service:
        """
        self.networking_service = networking_service
        self.deployment_service = deployment_service

    def delete_instance(self, logger, clients, kubernetes_name, deployed_app_name, namespace):
        """
        :param srr deployed_app_name:
        :param str namespace:
        :param Logger logger:
        :param KubernetesClients clients:
        :param str kubernetes_name:
        :rtype: None
        """
        self.networking_service.delete_internal_external_set(logger=logger,
                                                             clients=clients,
                                                             service_name_to_delete=kubernetes_name,
                                                             namespace=namespace)

        self.deployment_service.delete_app(logger=logger,
                                           clients=clients,
                                           namespace=namespace,
                                           app_name_to_delete=kubernetes_name)

        # wait untill the entire deployment doesnt exist any more before finishing the operation
        self.deployment_service.wait_until_exists(logger=logger,
                                                  clients=clients,
                                                  namespace=namespace,
                                                  app_name=kubernetes_name)

        logger.info("Deleted app {} with UID {} from ns/{}".format(deployed_app_name, kubernetes_name, namespace))
